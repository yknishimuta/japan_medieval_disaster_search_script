# 日本中世気象災害検索スクリプト

**このリポジトリは保守を終了する予定です。**

本プロジェクトは、藤木久志 編『日本中世気象災害史年表稿』（高志書院）の公開CSVデータを検索するPythonスクリプトです。「天変地異などの記事」のキーワード、地域、原出典、掲載書誌、グレゴリオ暦の範囲を組み合わせて検索できます。

現在は、ブラウザから検索・閲覧・CSV出力を行える[Web版](https://github.com/yknishimuta/japan_medieval_disaster_search_web)を後継として公開しています。本スクリプトはコマンドラインでの利用および参考資料として公開を継続しますが、新機能の追加や継続的な保守は予定していません。

## データの出典

- 藤木久志 編『日本中世気象災害史年表稿』（高志書院）
- データ公開：東京大学史料編纂所
- [公式データセット](https://lab.hi.u-tokyo.ac.jp/datasets/saigai)
- [DOI: 10.57459/hi.dg.disaster_events](https://doi.org/10.57459/hi.dg.disaster_events)

リポジトリに収録している `cmdjm-latest.csv` と、公式サイトで現在配布されているファイルが同一であるかは、このリポジトリでは保証していません。

## 動作環境とインストール

- Python 3
- pandas

仮想環境を使用する場合の例です。

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install pandas
```

Windowsでは、仮想環境の有効化に `.venv\Scripts\activate` を使用してください。

## 使い方

```bash
python search_disaster_events.py [検索ワード ...] [オプション]
```

検索ワードは「天変地異などの記事」に対する通常の文字列の部分一致検索です。複数指定すると、既定ではOR検索になります。検索ワードを省略した場合は、ほかの条件に一致するすべてのデータが対象です。

グレゴリオ暦が900年から1200年（境界を含む）で、「雨」を含むデータを検索する例：

```bash
python search_disaster_events.py 雨 -min 900 -max 1200
```

「雨」または「雷」を含むデータを検索する例：

```bash
python search_disaster_events.py 雨 雷
```

「雨」と「雷」の両方を含むデータを検索する例：

```bash
python search_disaster_events.py 雨 雷 --and-search
```

地域に「京都」を含むデータを検索する例：

```bash
python search_disaster_events.py -r 京都
```

原出典に「日本」を含むデータを検索する例：

```bash
python search_disaster_events.py -s 日本
```

原出典が「扶桑略記23」と完全一致するデータを検索する例：

```bash
python search_disaster_events.py -s 扶桑略記23 --strict-s
```

掲載書誌に「国史大系」を含むデータ、または指定値と完全一致するデータを検索する例：

```bash
python search_disaster_events.py -b 国史大系
python search_disaster_events.py -b 新訂増補国史大系 --strict-b
```

## オプション一覧

| オプション | 説明 |
| --- | --- |
| `-r 地域名` | 「地域」を部分一致で検索する |
| `-s 出典名` | 「原出典」を部分一致で検索する |
| `--strict-s` | `-s` で指定した「原出典」を完全一致で検索する |
| `-b 掲載書誌名` | 「掲載書誌」を部分一致で検索する |
| `--strict-b` | `-b` で指定した「掲載書誌」を完全一致で検索する |
| `-min 年`, `--min-year 年` | グレゴリオ暦の下限を指定する（指定年を含む） |
| `-max 年`, `--max-year 年` | グレゴリオ暦の上限を指定する（指定年を含む） |
| `--and-search` | 2個以上の検索ワードをAND検索にする |
| `-h`, `--help` | ヘルプを表示する |

地域・原出典・掲載書誌の部分一致検索と記事のキーワード検索では、正規表現ではなく入力した文字列をそのまま検索します。原出典または掲載書誌の完全一致検索には、それぞれ `-s` または `-b` と対応する `--strict-*` オプションを同時に指定してください。

## 年代検索

収録CSVの「グレゴリオ暦」は、区切りなしの `YYYMMDD` または `YYYYMMDD` 形式です。年代検索では、この形式から3桁または4桁の年部を解釈します。月日部に `00` が含まれていても、年部を解釈できる場合はその年として検索します。

空欄や形式外の値など、年部を解釈できないレコードは、年代条件を指定しない検索では保持されます。最小年または最大年を指定した検索では、恣意的な年に置き換えず検索対象外とします。

## 出力

検索結果は、実行時の作業ディレクトリにかかわらず、スクリプトと同じディレクトリにある `outputs/search_results.csv` にUTF-8 BOM付きで保存されます。`outputs` ディレクトリがなければ自動作成します。

検索結果が0件の場合も、列名だけを含むCSVで既存の出力ファイルを置き換えます。これにより、以前の検索結果が残っているように見えることを防ぎます。

## ライセンス

プログラムと収録データには異なるライセンスが適用されます。

- Pythonの独自ソースコード：[MIT License](LICENSE)
- `cmdjm-latest.csv` の収録データ：[Creative Commons Attribution 4.0 International（CC BY 4.0）](https://creativecommons.org/licenses/by/4.0/)

MIT Licenseは収録データには適用されません。データを利用する場合は、上記の出典を表示し、CC BY 4.0の条件に従ってください。
