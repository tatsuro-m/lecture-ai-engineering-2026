"""Use the same Pydantic AI agent and judge with the Mac's on-device model."""

import argparse
import json
import subprocess
from datetime import datetime
from functools import partial
from pathlib import Path

from pydantic_ai import DeferredToolRequests, DeferredToolResults, ToolDenied
from pydantic_ai.exceptions import UnexpectedModelBehavior, UsageLimitExceeded
from pydantic_ai.messages import (
    ModelRequest,
    ModelResponse,
    RetryPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.usage import UsageLimits

from app import agent, judge

MODEL = "apple-system-language-model"
TOOLS = {
    "search_glossary": "query",
    "get_lecture_summary": "lecture",
    "make_quiz": "lecture",
    "save_learning_log": "note",
}


def messages_for_bridge(messages):
    instructions = ""
    dialogue = []
    for message in messages:
        if isinstance(message, ModelRequest) and message.instructions:
            instructions = message.instructions
        for part in message.parts:
            if isinstance(part, UserPromptPart):
                dialogue.append(str(part.content))
            elif isinstance(part, ToolCallPart):
                dialogue.append(f"ツール呼び出し {part.tool_name}: {part.args_as_dict()}")
            elif isinstance(part, ToolReturnPart):
                dialogue.append(f"ツール結果 {part.tool_name}: {part.content}")
            elif isinstance(part, RetryPromptPart):
                dialogue.append(f"引数の修正が必要: {part.content}")
    return instructions, "\n\n".join(dialogue)


def request_model(bridge, instructions, prompt, mode, steps=()):
    payload = json.dumps(
        {"instructions": instructions, "prompt": prompt, "mode": mode, "steps": list(steps)},
        ensure_ascii=False,
    )
    run = subprocess.run([bridge], input=payload, text=True, capture_output=True, check=False, timeout=30)
    if run.returncode:
        raise RuntimeError(run.stderr.strip())
    return json.loads(run.stdout)


def agent_request(messages, info, *, bridge):
    instructions, prompt = messages_for_bridge(messages)
    visible_tools = {tool.name: tool for tool in info.function_tools}
    descriptions = []
    for name, parameter in TOOLS.items():
        tool = visible_tools.get(name)
        if tool:
            descriptions.append(f"- {name} ({parameter}): {tool.description}")
    instructions += (
        "\n\nツールが必要なら step に名前を指定し、対応する引数の欄に値を入れる。"
        "ツール結果で回答できるようになったら step を answer にし、answer 欄に回答を書く。"
        "\n利用可能なツール:\n" + "\n".join(descriptions)
    )
    previous_calls = sum(isinstance(part, ToolCallPart) for message in messages for part in message.parts)
    steps = ["answer", *visible_tools] if previous_calls < 2 else ["answer"]
    if previous_calls >= 2:
        instructions += "\nツールの実行回数の上限に達したので、今ある結果に基づき回答してください。"
    result = request_model(bridge, instructions, prompt, "agent", steps)
    if result["step"] == "answer":
        return ModelResponse(parts=[TextPart(result.get("answer") or "")])
    name = result["step"]
    parameter = TOOLS[name]
    return ModelResponse(parts=[ToolCallPart(name, {parameter: result.get(parameter)})])


def judge_request(messages, info, *, bridge):
    instructions, prompt = messages_for_bridge(messages)
    verdicts = request_model(bridge, instructions, prompt, "judge")
    return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name, verdicts)])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["generate", "judge"])
    parser.add_argument("cases", type=Path)
    parser.add_argument("--bridge", type=Path, required=True, help="compiled model.swift executable")
    parser.add_argument("--labels", type=Path, default=Path("lectures/04/my_labels.jsonl"))
    parser.add_argument("--out", type=Path, default=Path("lectures/04/my_judge_result.json"))
    args = parser.parse_args()
    cases = judge.read_jsonl(args.cases)
    if args.mode == "generate":
        model = FunctionModel(partial(agent_request, bridge=args.bridge.resolve()), model_name=MODEL)
        for case in cases:
            if case["answer"]:
                continue
            print(f"Generating #{case['id']}", flush=True)
            try:
                limits = UsageLimits(request_limit=8)
                result = agent.agent.run_sync(case["question"], model=model, usage_limits=limits)
                while isinstance(result.output, DeferredToolRequests):
                    result = agent.agent.run_sync(
                        model=model,
                        message_history=result.all_messages(),
                        deferred_tool_results=DeferredToolResults(
                            approvals={
                                call.tool_call_id: ToolDenied("評価中のため保存は承認しません。")
                                for call in result.output.approvals
                            }
                        ),
                        usage=result.usage,
                        usage_limits=limits,
                    )
                if not isinstance(result.output, str) or not result.output.strip():
                    raise RuntimeError(f"#{case['id']} did not return a final answer")
            except (RuntimeError, subprocess.TimeoutExpired, UsageLimitExceeded, UnexpectedModelBehavior) as error:
                print(f"#{case['id']}: {error}", flush=True)
                continue
            case["answer"] = result.output
            agent.print_trace(result)
            print(f"Generated #{case['id']}", flush=True)
            judge.write_jsonl(args.cases, cases)
        if any(not case["answer"].strip() for case in cases):
            raise SystemExit("未生成の回答があります。コマンドを再実行すると未生成分を処理します。")
    else:
        labels = judge.load_labels(args.labels)
        if any(not case["answer"].strip() or case["id"] not in labels for case in cases):
            raise SystemExit("全件の回答生成とラベル付けを終えてください。")
        model = FunctionModel(partial(judge_request, bridge=args.bridge.resolve()), model_name=MODEL)
        rubric = judge.DEFAULT_RUBRIC
        grader = judge.build_judge(model, rubric.read_text(encoding="utf-8"))
        verdicts = judge.judge_cases(grader, cases)
        summary = judge.summarize(cases, verdicts, labels)
        judge.print_summary(summary, labeler="Codex の基準ラベル")
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps(
                {
                    "model": MODEL,
                    "rubric": str(rubric.relative_to(judge.ROOT)),
                    "temperature": 0,
                    "run_at": datetime.now().isoformat(timespec="seconds"),
                    "verdicts": verdicts,
                    "summary": summary,
                },
                ensure_ascii=False, indent=2,
            ) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
