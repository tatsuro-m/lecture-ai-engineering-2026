# 第3回 解答

## 演習

Codexの補助を使い、ローカルのPython 3.12とGemini APIで実行した結果を記録した。比較には同じ `gemini-3.5-flash-lite` を使った。

第1回と同じ `AIE2026の講座の宿題にある「3レベル」とは何ですか？` と質問した。`app.ask` は一般的な難易度をもとに「基礎・応用・発展」と答え、どれか1つで完了するかは講座によるとした。`app.agent` は用語集を検索し、講座の「基礎・実装・発展」と、どれか1つに取り組めば完了することを答えた。

| 質問 | `--trace` のツール呼び出し | `requests` |
| --- | --- | ---: |
| 宿題の3レベル | `search_glossary(query="3レベル")` | 2 |
| LoRAとQLoRAの違い | `search_glossary(query="LoRA")`、`search_glossary(query="QLoRA")` | 2 |
| 第2回から確認問題を1問 | `make_quiz(lecture=2)` | 2 |

LoRAとQLoRAの検索は、1回目のモデル応答で2件まとめて呼ばれた。両方の結果を受け取ったモデルが、QLoRAではベースモデルを量子化してからLoRAで学習すると説明した。

`make_quiz` のdocstringには、指定した回の用語から確認問題を1問作り、問題と答えを返すことと、確認問題を頼まれたときに使うことを書いた。実行では第2回からエポックの意味が出題された。用語が存在しない回では、その旨を返す。

## 宿題

**実装レベル**に取り組んだ。`save_learning_log` を `requires_approval=True` で登録し、CLIに保存予定の本文を表示する。利用者の選択をツールの呼び出しIDに対応づけ、承認・拒否の結果とメッセージ履歴を渡して再開する。承認した本文は `learning_log/` のMarkdownファイルに保存する。

Gemini APIで同じ保存依頼を2回実行した。`n` で拒否した場合の作成は0件、`y` で承認した場合は1件で、ファイルの本文は承認画面の本文と一致した。どちらも `requests=2` だった。模擬モデルでも承認待ちの時点では保存されず、入力を閉じた場合は拒否として扱われることを確認した。既存テストは11件すべて通過した。

元の依頼と同じ文面で保存するようツール説明に書いても、モデルが見出しなどを補うことがあった。本文を表示してから承認を受けることで、利用者が実際に保存される内容を確認できる。

手元の `.env` からAPIキーを渡して再現する。

```sh
uv run --env-file .env python -m app.ask 'AIE2026の講座の宿題にある「3レベル」とは何ですか？'
uv run --env-file .env python -m app.agent --trace 'AIE2026の講座の宿題にある「3レベル」とは何ですか？'
uv run --env-file .env python -m app.agent --trace 'LoRAとQLoRAの違いは？'
uv run python -m app.agent --list-tools
uv run --env-file .env python -m app.agent --trace '第2回の内容から確認問題を1問出して'
uv run --env-file .env python -m app.agent --trace '第3回の学習記録として「モデルがツールを選び、ハーネスが実行する。」をそのまま保存して。'
uv run pytest -q
```
