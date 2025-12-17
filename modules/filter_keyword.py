"""
filter_keyword.py - キーワードフィルタリングモジュール

責務:
- temp_extracted/*.csv から [RT_IDP_ATTACK] を含む行のみ抽出
- filtered_logs/*.csv に出力
"""

import csv
from pathlib import Path
from typing import List


class FilterError(Exception):
    """フィルタリング時のカスタム例外"""
    pass


def filter_csv_by_keyword(input_path: Path, output_path: Path, keyword: str) -> int:
    """
    単一CSVファイルからキーワードを含む行のみ抽出
    
    Args:
        input_path: 入力CSVファイルのパス
        output_path: 出力CSVファイルのパス
        keyword: フィルタリングするキーワード
        
    Returns:
        抽出された行数
        
    Raises:
        FilterError: フィルタリングに失敗した場合
        FileNotFoundError: 入力ファイルが存在しない場合
    """
    if not input_path.exists():
        raise FileNotFoundError(f"入力ファイルが見つかりません: {input_path}")
    
    # 出力ディレクトリが存在しない場合は作成
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        filtered_rows = []
        header = None
        
        # CSVを読み込み
        with open(input_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.reader(f)
            
            # ヘッダー行を取得
            header = next(reader, None)
            if header is None:
                raise FilterError(f"CSVファイルが空です: {input_path}")
            
            # キーワードを含む行のみフィルタリング
            for row in reader:
                # Message列（7列目、インデックス6）にキーワードが含まれているか確認
                if len(row) > 6 and keyword in row[6]:
                    filtered_rows.append(row)
        
        # フィルタリング結果を出力
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(filtered_rows)
        
        return len(filtered_rows)
        
    except Exception as e:
        raise FilterError(f"フィルタリング中にエラーが発生しました: {input_path}, エラー: {str(e)}")


def filter_keyword(csv_files: List[Path], output_dir: Path, keyword: str = "RT_IDP_ATTACK", verbose: bool = False) -> int:
    """
    複数のCSVファイルからキーワードを含む行のみ抽出
    
    Args:
        csv_files: 入力CSVファイルのパスリスト
        output_dir: 出力ディレクトリ
        keyword: フィルタリングするキーワード
        verbose: 詳細ログを出力するか
        
    Returns:
        全ファイルで抽出された総行数
        
    Raises:
        FilterError: フィルタリングに失敗した場合
    """
    if not csv_files:
        if verbose:
            print("⚠️  フィルタリングするCSVファイルがありません")
        return 0
    
    total_filtered = 0
    success_count = 0
    error_count = 0
    
    for csv_path in csv_files:
        try:
            if verbose:
                print(f"🔍 フィルタリング中: {csv_path.name}...", end=" ")
            
            # 出力ファイル名は入力ファイル名と同じ
            output_path = output_dir / csv_path.name
            
            filtered_count = filter_csv_by_keyword(csv_path, output_path, keyword)
            total_filtered += filtered_count
            success_count += 1
            
            if verbose:
                print(f"✓ ({filtered_count}行抽出)")
                
        except (FilterError, FileNotFoundError) as e:
            error_count += 1
            if verbose:
                print(f"✗ エラー: {str(e)}")
    
    if verbose:
        print(f"\n✅ フィルタリング完了: {success_count}個成功, {error_count}個失敗")
        print(f"📊 総抽出行数: {total_filtered}行")
    
    return total_filtered


def main():
    """
    スタンドアロン実行用のメイン関数
    """
    # デフォルトパス設定
    project_root = Path(__file__).parent.parent
    input_dir = project_root / "temp_extracted"
    output_dir = project_root / "filtered_logs"
    
    print("=" * 60)
    print("Juniper Syslog Filter - キーワードフィルタリングモジュール")
    print("=" * 60)
    
    try:
        # 入力CSVファイルを取得
        csv_files = sorted(input_dir.glob("*.csv"))
        
        if not csv_files:
            print(f"\n⚠️  CSVファイルが見つかりませんでした: {input_dir}")
            return 0
        
        print(f"\n対象ファイル数: {len(csv_files)}")
        print(f"フィルタリングキーワード: RT_IDP_ATTACK")
        print()
        
        total_filtered = filter_keyword(csv_files, output_dir, keyword="RT_IDP_ATTACK", verbose=True)
        
        if total_filtered > 0:
            print(f"\n✅ 処理完了: {total_filtered}行を抽出しました")
        else:
            print("\n⚠️  抽出された行がありません")
            
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())