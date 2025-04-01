import csv
import pandas as pd
import argparse

input_file_path = "./cmdjm-latest.csv" 
output_path = "./outputs/search_results.csv"
gregorian_col_name = 'グレゴリオ暦'
source_col_name = '原出典'
bibliography_col_name = '掲載書誌'
event_col_name = '天変地異などの記事'

def filter_data(file_path, event_keywords=None, source_name=None, bibliography_name=None, min_year=None, max_year=None,
                source_exact_match=False, bibliography_exact_match=False, and_search=False):

    df = pd.read_csv(file_path, header=0, encoding='utf-8') 
    df['year'] = df[gregorian_col_name].astype(str).apply(lambda x: int(x[:3]) if len(x) == 7 else int(x[:4]))
    df[source_col_name] = df[source_col_name].fillna("")
    df[bibliography_col_name] = df[bibliography_col_name].fillna("")
    df[event_col_name] = df[event_col_name].fillna("")
    
    if event_keywords:
        keywords_list = event_keywords
        if and_search:
            df = df[df[event_col_name].apply(lambda x: all(kw in x for kw in keywords_list))]
        else:
            df = df[df[event_col_name].apply(lambda x: any(kw in x for kw in keywords_list))]

    if source_name:
        if source_exact_match:
            df = df[df[source_col_name] == source_name]
        else:
            df = df[df[source_col_name].str.contains(source_name)]
        
    if bibliography_name:
        if bibliography_exact_match:
            df = df[df[bibliography_col_name] == bibliography_name]
        else:
            df = df[df[bibliography_col_name].str.contains(bibliography_name)]
            
    
    if min_year is not None:
        df = df[df['year'] >= min_year]
    if max_year is not None:
        df = df[df['year'] <= max_year]
    
    df = df.drop(columns=['year'])
    filtered_data = df.values.tolist()
    filtered_data.insert(0, df.columns.tolist())
    
    return filtered_data


def save_filtered_data(filtered_data, output_path):
    if len(filtered_data) <= 1:
        print("指定された条件でデータが見つかりませんでした")
        return
    
    with open(output_path, mode='w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(filtered_data)
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

# main part
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="『日本中世気象災害史年表稿』の詳細検索スクリプト")
    parser.add_argument("event_keywords", nargs="*", default=None, help="検索する天変地異などの記事のキーワード（複数可）")
    parser.add_argument("-s", dest="source_name", type=str, default=None, help="原出典の検索ワード（部分一致）")
    parser.add_argument("--strict-s", dest="source_exact_match", action="store_true", help="原出典の完全一致検索を有効にする")
    parser.add_argument("-b", dest="bibliography_name", type=str, default=None, help="掲載書誌の検索ワード（部分一致）")
    parser.add_argument("--strict-b", dest="bibliography_exact_match", action="store_true", help="掲載書誌の完全一致検索を有効にする")
    parser.add_argument("-min", "--min-year", type=int, default=None, help="グレゴリオ暦の最小年")
    parser.add_argument("-max", "--max-year", type=int, default=None, help="グレゴリオ暦の最大年")
    parser.add_argument("--and-search", action="store_true", help="AND検索を有効にする")

    args = parser.parse_args()

    validate_source_name(args)
    validate_bibliography_name(args)
    validate_and_search(args)
    
    filtered_data = filter_data(input_file_path, args.event_keywords, args.source_name, args.bibliography_name,
                        args.min_year, args.max_year, source_exact_match=args.source_exact_match,
                        bibliography_exact_match=args.bibliography_exact_match, and_search=args.and_search)
    
    save_filtered_data(filtered_data, output_path)