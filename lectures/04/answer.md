# 第4回 解答

## 演習

配布された10件をローカルの Streamlit で開き、Codex が参照とルーブリックを読んで5基準のラベルを入力した。講師ラベルとの比較は保存後に行った。Gemini の採点には、既定の `gemini-3.5-flash-lite` が混雑エラーを繰り返したため、修正前後とも `gemini-3.1-flash-lite` を使った。

#05 の回答は、RAG が用語集にないと明記したうえで一般的な意味を説明していた。暫定で根拠を合格とし、判断に迷ったことを記録した。`data/eval/rubric.md` の根拠に、未収録と断ったうえで一般的に説明してよいという一文を加え、未決事項からこの論点を外した。比較には同じ評価セットとラベルを使った。

| 項目 | 修正前 | 修正後 |
| --- | ---: | ---: |
| 根拠 | 7/9 | 8/10 |
| 範囲 | 10/10 | 10/10 |
| ヒント | 10/10 | 10/10 |
| 分かりやすさ | 9/10 | 9/10 |
| 回の表示（コード） | 10/10 | 10/10 |
| 総合の一致 | 9/9 | 10/10 |
| 自動判定できた割合 | 90% | 100% |
| 要確認 | 1件 | 0件 |

#05 の根拠は `unsure` から `pass` に変わった。修正後も #04 の説明の繰り返しを Gemini は見逃し、#06 の完成コードと #08 の範囲違反を根拠にも持ち込んだ。#06 と #08 はヒントや範囲でどちらの採点者も総合不合格にしたため、根拠の不一致は総合一致率に現れなかった。

講師ラベルとは5基準すべてで10/10件一致した。「迷った」の記録は Codex が #05、講師が #04・#05・#07 だった。#04 の同じ説明の繰り返しは、ルーブリックに明記された不合格条件として扱った。#07 は講座外の質問を適切に断っているが、回の表示は「第N回」がないため形式上は不合格とした。

判定と理由は [修正前](judge_result_before.json) と [修正後](judge_result.json) に保存した。修正前の基準は講座の第4回開始コミットから取得できる。

```sh
uv run --with streamlit==1.66.1 streamlit run tools/annotate.py
uv run python -m app.judge --compare lectures/04/reference/labels_instructor.jsonl

before_rubric=$(mktemp)
git show cf0e2c3:data/eval/rubric.md > "$before_rubric"
uv run --env-file .env python -m app.judge --model gemini-3.1-flash-lite --wait 2 \
  --rubric "$before_rubric" --out /tmp/lec04-judge-before.json
uv run --env-file .env python -m app.judge --model gemini-3.1-flash-lite --wait 2 \
  --out /tmp/lec04-judge-after.json
rm "$before_rubric"
```

## 宿題

**実装レベル**に取り組んだ。第3回で作った学習支援エージェント向けに、サブエージェントと質問・期待する振る舞いを10件作り、別のサブエージェントが用語集の参照と期待する振る舞いをレビューした。用語の説明や講義要約に加え、表記ゆれ、誤った前提、出題対象のない回、完成コードの要求、講座内外の混在、架空の用語を含めた。第3回に追加した確認問題と学習記録の承認についても、正解を明かさずに出題できるか、保存を依頼せずに承認の挙動を説明できるかを問うた。

宿題は Apple のオンデバイスモデル `SystemLanguageModel` で回答を生成し、同じモデルに第4回の改訂後のルーブリックで採点させた。第3回の `app.agent` にローカルモデルを接続し、ツール呼び出しは1件あたり2回までとした。Codex とサブエージェントが回答を読んで判定し、Streamlit に基準ラベルを10件保存した。演習と宿題では採点モデルとデータセットの両方が異なる。

| 基準 | 一致 |
| --- | ---: |
| 根拠 | 5/10 |
| 範囲 | 8/10 |
| ヒント | 6/10 |
| 分かりやすさ | 5/10 |
| 回の表示（コード） | 10/10 |
| 総合の一致 | 7/10 |
| 自動判定できた割合 | 100% |
| 要確認 | 0件 |

基準別では16件の不一致があった。#06 の根拠は、採点理由では出題できないと伝えた点を「期待されるふるまいに合致」と評価しながら、判定は `fail` だった。#08 のヒントでは、回答にない承認結果と会話履歴の手順を提示したと読んで `pass` にした。要確認が0件でも、理由と判定の矛盾や、回答にない記述の読み込みは残る。判定ごとの理由は [my_judge_result.json](my_judge_result.json) に保存した。

#05 は確認問題の答えを先に表示した。クイズの答え漏れには専用の基準がないため、現行のルーブリックでは分かりやすさで不合格とし、ヒントは宿題と無関係なので合格とした。#07 は保存しないよう求めたのに保存ツールの承認要求が2回発生した。どちらも拒否し、保存先のファイルは0件だった。最終回答には承認要求が現れないため、この失敗はツール履歴で確認した。

### コードで判定する項目と、LLMに任せる項目

最終行に「第N回」があるかは正規表現で確認できる。演習の #10 は存在しない「第14回」でも形式上は合格した。回番号の正しさも評価する場合は、ケースごとの期待値と照合し、該当する回がないときの表記も先に決める。確認問題の問題数や答え欄の有無は、構造化した出力をコードで確認できる。学習記録の承認や書き込みの有無は、ツールの実行履歴と保存先の状態を確認する。

用語集への忠実さ、講座内外が混在する依頼の切り分け、完成コードを渡さずにヒントを示せたかは、表現に幅があるので、参照と合否条件を渡して LLM で判定する。根拠が足りない場合や判定が割れた場合は、該当する回答と採点理由を確認する。

### 再実行

回答付きの評価セットは [my_cases.jsonl](../../data/eval/my_cases.jsonl)、ラベルは [my_labels.jsonl](my_labels.jsonl)。同じ回答を再採点するには、Apple Intelligence が利用できる macOS でリポジトリのルートから次を実行する。

```sh
run_dir=$(mktemp -d)
swiftc lectures/04/on_device/model.swift -o "$run_dir/model"
PYTHONPATH=. uv run python lectures/04/on_device/run.py judge data/eval/my_cases.jsonl \
  --bridge "$run_dir/model" --out "$run_dir/my_judge_result.json"
```

回答を生成し直す場合は、回答欄を空にしたコピーを使う。生成し直した回答には新しいラベルを付ける。確認問題で選ばれる用語はツール内でランダムに決まる。

```sh
uv run python - "$run_dir/cases.jsonl" <<'PY'
from pathlib import Path
import sys

from app.judge import read_jsonl, write_jsonl

cases = read_jsonl(Path("data/eval/my_cases.jsonl"))
for case in cases:
    case["answer"] = ""
write_jsonl(Path(sys.argv[1]), cases)
PY
PYTHONPATH=. uv run python lectures/04/on_device/run.py generate "$run_dir/cases.jsonl" \
  --bridge "$run_dir/model"
```
