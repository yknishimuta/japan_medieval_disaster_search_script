import csv
import argparse
import re
import sys
from numbers import Integral, Real
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_FILE_PATH = SCRIPT_DIR / "cmdjm-latest.csv"
OUTPUT_PATH = SCRIPT_DIR / "outputs" / "search_results.csv"
gregorian_col_name = 'グレゴリオ暦'
region_col_name = '地域'
source_col_name = '原出典'
bibliography_col_name = '掲載書誌'
event_col_name = '天変地異などの記事'

gregorian_date_pattern = re.compile(
    r"^(?P<year>[0-9]{3,4})(?P<month>[0-9]{2})(?P<day>[0-9]{2})$"
)


def extract_year(value):
    """YYYMMDDまたはYYYYMMDD形式の値から年を取り出す。"""
    if pd.isna(value):
        return pd.NA

    if isinstance(value, Integral) and not isinstance(value, bool):
        text = str(value)
    elif isinstance(value, Real) and value.is_integer():
        text = str(int(value))
    else:
        text = str(value).strip()

    match = gregorian_date_pattern.fullmatch(text)
    if match is None:
        return pd.NA
    return int(match.group("year"))

def filter_data(file_path, event_keywords=None, region_name=None, source_name=None, bibliography_name=None, min_year=None, max_year=None,
                source_exact_match=False, bibliography_exact_match=False, and_search=False):

    df = pd.read_csv(
        file_path,
        header=0,
        encoding='utf-8',
        dtype={gregorian_col_name: "string"},
    )
    df['year'] = df[gregorian_col_name].apply(extract_year)
    for column_name in (
        region_col_name,
        source_col_name,
        bibliography_col_name,
        event_col_name,
    ):
        df[column_name] = df[column_name].fillna("")
    
    if event_keywords:
        if and_search:
            for keyword in event_keywords:
                df = df[
                    df[event_col_name].str.contains(keyword, regex=False, na=False)
                ]
        else:
            matches = pd.Series(False, index=df.index)
            for keyword in event_keywords:
                matches |= df[event_col_name].str.contains(
                    keyword, regex=False, na=False
                )
            df = df[matches]

    if region_name:
        df = df[df[region_col_name].str.contains(region_name, regex=False, na=False)]

    if source_name:
        if source_exact_match:
            df = df[df[source_col_name] == source_name]
        else:
            df = df[
                df[source_col_name].str.contains(source_name, regex=False, na=False)
            ]
        
    if bibliography_name:
        if bibliography_exact_match:
            df = df[df[bibliography_col_name] == bibliography_name]
        else:
            df = df[
                df[bibliography_col_name].str.contains(
                    bibliography_name, regex=False, na=False
                )
            ]
            
    
    if min_year is not None:
        df = df[df['year'].ge(min_year).fillna(False)]
    if max_year is not None:
        df = df[df['year'].le(max_year).fillna(False)]
    
    df = df.drop(columns=['year'])
    filtered_data = df.values.tolist()
    filtered_data.insert(0, df.columns.tolist())
    
    return filtered_data


def save_filtered_data(filtered_data, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open(mode='w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(filtered_data)

    if len(filtered_data) <= 1:
        print("指定された条件でデータが見つかりませんでした")
    else:
        print(f"{len(filtered_data) - 1} 件のデータが見つかりました")
    print(f"検索結果を {output_path} に保存しました")

def validate_source_name(args):
    """--strict-sが指定されているが-sが指定されていない場合はエラー"""
    if args.source_exact_match and not args.source_name:
        print ("--strict-sを指定する場合は、-s も指定してください")
        exit(1)

def validate_bibliography_name(args):
    """--strict-sが指定されているが-sが指定されていない場合はエラー"""
    if args.bibliography_exact_match and not args.bibliography_name:
        print ("--strict-bを指定する場合は、-b も指定してください")
        exit(1)

def validate_and_search(args):
    """--and-searchが指定されているがキーワードが2つより少ない場合はエラー"""
    if args.and_search and (len(args.event_keywords) < 2):
        print("--and-searchを使用する場合は記事のキーワードを2つ以上指定してください")
        exit(1)


def create_parser():
    parser = argparse.ArgumentParser(description="『日本中世気象災害史年表稿』の詳細検索スクリプト")
    parser.add_argument("event_keywords", nargs="*", default=None, help="検索する天変地異などの記事のキーワード（複数可）")
    parser.add_argument("-r", dest="region_name", type=str, default=None, help="地域の検索ワード")
    parser.add_argument("-s", dest="source_name", type=str, default=None, help="原出典の検索ワード（部分一致）")
    parser.add_argument("--strict-s", dest="source_exact_match", action="store_true", help="原出典の完全一致検索を有効にする")
    parser.add_argument("-b", dest="bibliography_name", type=str, default=None, help="掲載書誌の検索ワード（部分一致）")
    parser.add_argument("--strict-b", dest="bibliography_exact_match", action="store_true", help="掲載書誌の完全一致検索を有効にする")
    parser.add_argument("-min", "--min-year", type=int, default=None, help="グレゴリオ暦の最小年")
    parser.add_argument("-max", "--max-year", type=int, default=None, help="グレゴリオ暦の最大年")
    parser.add_argument("--and-search", action="store_true", help="AND検索を有効にする")
    return parser


def main(argv=None, input_path=INPUT_FILE_PATH, output_path=OUTPUT_PATH):
    parser = create_parser()
    args = parser.parse_args(argv)

    validate_source_name(args)
    validate_bibliography_name(args)
    validate_and_search(args)

    input_path = Path(input_path)
    if not input_path.is_file():
        print(f"入力CSVが見つかりません: {input_path}", file=sys.stderr)
        return 1

    filtered_data = filter_data(
        input_path,
        args.event_keywords,
        args.region_name,
        args.source_name,
        args.bibliography_name,
        args.min_year,
        args.max_year,
        source_exact_match=args.source_exact_match,
        bibliography_exact_match=args.bibliography_exact_match,
        and_search=args.and_search,
    )
    save_filtered_data(filtered_data, output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
