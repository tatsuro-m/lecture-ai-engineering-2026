"""第1回: LLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする
    uv run python -m app.ask --chat     # 会話履歴を保って質問を続ける

通常はツールも会話履歴も持たない「素の」呼び出し。--chat では履歴を保持する。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse

from google import genai
from google.genai import errors, types

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def ask(question: str) -> str:
    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(model=MODEL, contents=question)

    print_usage(response)
    return response.text


def print_usage(response: types.GenerateContentResponse) -> None:
    """1回のリクエストの入力・出力トークン数を表示する。"""
    usage = response.usage_metadata
    if usage is not None:
        input_tokens = usage.prompt_token_count
        output_tokens = usage.candidates_token_count
        print(f"[入力トークン数] {input_tokens if input_tokens is not None else '取得できませんでした'}")
        print(f"[出力トークン数] {output_tokens if output_tokens is not None else '取得できませんでした'}\n")
    else:
        print("[トークン数] 取得できませんでした\n")


def chat(initial_question: str | None = None) -> None:
    """同じセッションを使い、ユーザーとモデルの会話履歴を次の質問に渡す。"""
    client = genai.Client(api_key=get_api_key())
    session = client.chats.create(model=MODEL)
    print("会話モードです。終了するには /exit または /quit を入力してください。")
    question = initial_question
    while True:
        if question is None:
            try:
                question = input("あなた> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n会話を終了します。")
                return
        if question.strip().lower() in ("/exit", "/quit"):
            return
        if question.strip():
            print(f"[質問] {question}\n")
            response = session.send_message(question)
            print_usage(response)
            print(f"Gemini> {response.text}\n")
        question = None


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", help="質問（--chat では最初の質問）")
    parser.add_argument("--chat", action="store_true", help="会話履歴を保って質問を続ける")
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    try:
        if args.chat:
            chat(args.question)
        else:
            question = args.question if args.question is not None else DEFAULT_QUESTION
            print(f"[質問] {question}\n")
            print(ask(question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
