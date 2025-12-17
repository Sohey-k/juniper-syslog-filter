"""
merge_files.py - ファイルマージモジュール

責務:
- filtered_logs/*.csv を読み込み
- 80万行単位でマージ
- merged_logs/merged_001.csv, merged_002.csv... に出力
"""

import csv
from pathlib import Path
from typing import List


class MergeError(Exception):
    """マージ時のカスタム例外"""
    pass


def merge_csv_files(input_files: List[Path], output_dir: Path, max_rows: int = 800000, verbose: bool = False) -> List[Path]:
    """
    複数のCSVファイルを80万行単位でマージ
    
    Args:
        input_files: 入力CSVファイルのリスト
        output_dir: 出力ディレクトリ
        max_rows: 1ファイルあたりの最大行数（デフォルト: 80万行）
        verbose: 詳細ログを出力するか
        
    Returns:
        出力されたファイルのリスト
        
    Raises:
        MergeError: マージに失敗した場合
        FileNotFoundError: 入力ファイルが存在しない場合
    """
    if not input_files:
        if verbose:
            print("⚠️  マージするファイルがありません")
        return []
    
    # 出力ディレクトリが存在しない場合は作成
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_files = []
    current_file_index = 1
    current_row_count = 0
    current_writer = None
    current_file = None
    header = None
    
    try:
        for input_file in sorted(input_files):
            if not input_file.exists():
                raise FileNotFoundError(f"入力ファイルが見つかりません: {input_file}")
            
            if verbose:
                print(f"📄 読み込み中: {input_file.name}")
            
            with open(input_file, 'r', encoding='utf-8', newline='') as f:
                reader = csv.reader(f)
                
                # ヘッダー行を取得
                file_header = next(reader, None)
                if file_header is None:
                    continue
                
                # 最初のファイルからヘッダーを保存
                if header is None:
                    header = file_header
                
                # データ行を処理
                for row in reader:
                    # 新しいファイルを開く必要があるか？
                    if current_writer is None or current_row_count >= max_rows:
                        # 既存のファイルを閉じる
                        if current_file:
                            current_file.close()
                        
                        # 新しいファイルを開く
                        output_filename = f"merged_{current_file_index:03d}.csv"
                        output_path = output_dir / output_filename
                        current_file = open(output_path, 'w', encoding='utf-8', newline='')
                        current_writer = csv.writer(current_file)
                        
                        # ヘッダーを書き込み
                        current_writer.writerow(header)
                        
                        output_files.append(output_path)
                        current_row_count = 0
                        current_file_index += 1
                        
                        if verbose:
                            print(f"  ✓ 新規ファイル作成: {output_filename}")
                    
                    # データ行を書き込み
                    current_writer.writerow(row)
                    current_row_count += 1
        
        # 最後のファイルを閉じる
        if current_file:
            current_file.close()
        
        if verbose:
            print(f"\n✅ マージ完了: {len(output_files)}個のファイルを作成")
            for i, output_file in enumerate(output_files, 1):
                print(f"  {i}. {output_file.name}")
        
        return output_files
        
    except Exception as e:
        # エラー時はファイルを閉じる
        if current_file:
            current_file.close()
        raise MergeError(f"マージ中にエラーが発生しました: {str(e)}")


def main():
    """
    スタンドアロン実行用のメイン関数
    """
    # デフォルトパス設定
    project_root = Path(__file__).parent.parent
    input_dir = project_root / "filtered_logs"
    output_dir = project_root / "merged_logs"
    
    print("=" * 60)
    print("Juniper Syslog Filter - マージモジュール")
    print("=" * 60)
    
    try:
        # 入力CSVファイルを取得
        csv_files = sorted(input_dir.glob("*.csv"))
        
        if not csv_files:
            print(f"\n⚠️  CSVファイルが見つかりませんでした: {input_dir}")
            return 0
        
        print(f"\n対象ファイル数: {len(csv_files)}")
        print(f"最大行数/ファイル: 800,000行")
        print()
        
        output_files = merge_csv_files(csv_files, output_dir, max_rows=800000, verbose=True)
        
        if output_files:
            print(f"\n✅ 処理完了: {len(output_files)}個のマージファイルを作成しました")
        else:
            print("\n⚠️  マージするデータがありませんでした")
            
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())