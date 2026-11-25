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

- 取り組んだレベル：基礎 / 実装 / 発展
- やったこと：
- 結果：
- 気づき・疑問：
