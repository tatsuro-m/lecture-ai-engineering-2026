"""APIを呼ばず、会話履歴の送信とCLIの終了動作を確かめる。"""

from unittest.mock import Mock

import pytest
from google import genai
from google.genai import errors, types

from app import ask


def response(text):
    return types.GenerateContentResponse(
        candidates=[types.Candidate(
            content=types.Content(role="model", parts=[types.Part(text=text)]),
            finish_reason="STOP",
        )],
        usage_metadata=types.GenerateContentResponseUsageMetadata(
            prompt_token_count=12, candidates_token_count=34,
        ),
    )


@pytest.fixture
def client(monkeypatch):
    client = genai.Client(api_key="test-key")
    generate = Mock(side_effect=[response("青です。"), response("青です。")])
    monkeypatch.setattr(client.models, "generate_content", generate)
    monkeypatch.setattr(ask.genai, "Client", lambda **kwargs: client)
    monkeypatch.setattr(ask, "get_api_key", lambda: "test-key")
    yield client
    client.close()


def test_chat_sends_user_and_model_history(client, monkeypatch, capsys):
    inputs = iter(["私の好きな色は青です。", "私の好きな色は？", "/exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    ask.chat()
    calls = client.models.generate_content.call_args_list
    assert len(calls) == 2
    history = calls[1].kwargs["contents"]
    assert [(c.role, c.parts[0].text) for c in history] == [
        ("user", "私の好きな色は青です。"),
        ("model", "青です。"),
        ("user", "私の好きな色は？"),
    ]
    assert "[入力トークン数] 12" in capsys.readouterr().out


@pytest.mark.parametrize("ending", ["/exit", "/quit", EOFError(), KeyboardInterrupt()])
def test_chat_blank_and_exit_do_not_call_api(client, monkeypatch, ending):
    inputs = Mock(side_effect=["   ", ending])
    monkeypatch.setattr("builtins.input", inputs)
    ask.chat()
    client.models.generate_content.assert_not_called()


def test_cli_chat_initial_question(client, monkeypatch):
    monkeypatch.setattr("sys.argv", ["ask", "--chat", "色を教えて"])
    monkeypatch.setattr("builtins.input", lambda _: "/quit")
    ask.main()
    assert client.models.generate_content.call_count == 1


def test_cli_keeps_default_single_question(client, monkeypatch):
    monkeypatch.setattr("sys.argv", ["ask"])
    ask.main()
    assert client.models.generate_content.call_args.kwargs["contents"] == ask.DEFAULT_QUESTION


def test_cli_reports_chat_api_error(client, monkeypatch, capsys):
    client.models.generate_content.side_effect = errors.ClientError(429, {"error": {"message": "quota"}})
    monkeypatch.setattr("sys.argv", ["ask", "--chat", "質問"])
    with pytest.raises(SystemExit, match="1"):
        ask.main()
    assert "レート制限" in capsys.readouterr().out
