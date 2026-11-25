# 第6回 解答

## 演習

<!-- [tool call] の行は、表示された行をそのまま貼り付けてください。終わらなかった STEP は、空欄のままでかまいません。 -->

- STEP 1 のツールの名前：glossary_search_glossary
- STEP 2 の [tool call]：glossary_search_glossary({'query': '3レベル'})
- STEP 3 の [tool call]：fetch_fetch({'url': 'https://modelcontextprotocol.io/'})
- STEP 4 の [tool call]：
  - `aws_aws___search_documentation({'search_phrase': 'Amazon S3 バージョニング'})`
  - `aws_aws___search_documentation({'search_phrase': 'What is versioning in Amazon S3', 'topics': ['general']})`
- 気づき・疑問：エージェント側のコードを一切変えずに、`app/mcp_servers.json` に数行追加するだけでローカル起動（`uv` / `uvx`）とリモート接続（`url`）のツールを同じ形で扱える点が便利だった。一方で、STEP 2（1ツール・入力709 tokens）から STEP 3（2ツール・2,224 tokens）、STEP 4（7ツール・11,280 tokens）とサーバーを増やすにつれてツール定義だけで入力トークンが大きく増えることも確認できた。また、STEP 4 では最初の日本語クエリで適切な記事が引けなかった後に、モデルが英語クエリへ言い換えて再検索していた。

## 宿題

<!-- 基礎・実装・発展のどれか1つに取り組めば完了です。 -->

- 取り組んだレベル：実装
- やったこと：
  1. `app/mcp_server.py` に `server.tool()(tools.make_quiz)` を追加し、第3回で作成した `make_quiz` を MCP サーバーのツール（`glossary_make_quiz`）として公開した（エージェント側の `app/mcp_agent.py`・`app/mcp_servers.json` は変更していない）。
  2. `app/tools.py` の `make_quiz` で、用語集に該当する回が存在しない場合（範囲外や未登録の回）に、単に作れない旨だけでなく用語集から動的に取得した有効な回の一覧（`指定できる回: 第1回, 第2回, 第3回, 第4回, 第6回`）を `return` で返すように改善した。
  3. `--list-tools`、正常系（`第2回のクイズを作って`）、範囲外（`第99回のクイズを作って`）、境界値（`0`, `-1`, `5`, `99`）、および比較として例外（`raise ValueError`）を投げた場合の挙動を確認した。
- 結果：
  - `--list-tools` でエージェント側を変更せずに `glossary_make_quiz` が一覧に表示された（引数 `{"lecture": {"title": "Lecture", "type": "integer"}}`）。
  - 正常系（`uv run python -m app.mcp_agent --trace "第2回のクイズを作って"`）：
    - `[tool call]   glossary_make_quiz({'lecture': 2})`
    - `[tool return] glossary_make_quiz -> {"question": "「QLoRA」の意味は？", "answer": ...`
    - 応答：「第2回の確認問題はこちらです！ **問題：** 「QLoRA」の意味は？」（モデル応答 2 回、入力 5,521 tokens / 出力 54 tokens）
  - 範囲外（`uv run python -m app.mcp_agent --trace "第99回のクイズを作って"`）：
    - `[tool call]   glossary_make_quiz({'lecture': 99})`
    - `[tool return] glossary_make_quiz -> 第99回の用語は用語集に登録されていないため、確認問題を作れません。指定できる回: 第1回, 第2回, 第3回, 第4回, 第6回`
    - 応答：「第99回は用語集に登録されていないため、確認問題を作成することができません。」に続けて、指定可能な第1・2・3・4・6回を箇条書きで案内した（モデル応答 2 回、入力 5,473 tokens / 出力 95 tokens）。
  - 既存テスト `uv run pytest -q` は 21 件すべて通過した。
- 気づき・疑問：
  - `return` で「作れない理由」と「指定できる有効な回の一覧」を返すと、`[tool return]` としてそのままモデルに伝わり、モデルが推測で架空の問題を作ることなく、正しい選択肢をユーザーに案内できた（用語集に第5回が未登録であることも動的に反映された）。
  - 比較として同じ条件で `raise ValueError` を投げる実験を行ったところ、ツールエラーとしてリトライが発生し、`max_retries`（既定1回）を超過して `UnexpectedModelBehavior` で実行が停止した。想定内の範囲外入力は例外で落とさず、直し方が分かるメッセージを `return` で返す方がエージェントの挙動が安定することが分かった。
