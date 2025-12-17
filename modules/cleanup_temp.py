"""
cleanup_temp.py - 一時ファイル削除モジュール

責務:
- 処理済みのZIPファイルを削除（source_logs/）
- 展開された一時CSVファイルを削除（temp_extracted/）
"""

import os
from pathlib import Path
from typing import List


class CleanupError(Exception):
    """クリーンアップ時のカスタム例外"""
    pass


def cleanup_processed_files(zip_path: Path, csv_files: List[Path], verbose: bool = False) -> bool:
    """
    処理済みのZIPファイルと展開されたCSVファイルを削除
    
    Args:
        zip_path: 削除するZIPファイルのパス
        csv_files: 削除するCSVファイルのリスト
        verbose: 詳細ログを出力するか
        
    Returns:
        成功したらTrue、失敗したらFalse
        
    Raises:
        CleanupError: クリーンアップに失敗した場合
    """
    success = True
    
    try:
        # ZIPファイルを削除
        if zip_path.exists():
            zip_path.unlink()
            if verbose:
                print(f"  削除: {zip_path.name}")
        else:
            if verbose:
                print(f"  ⚠️  ZIPファイルが見つかりません: {zip_path}")
            success = False
        
        # CSVファイルを削除
        for csv_file in csv_files:
            if csv_file.exists():
                csv_file.unlink()
                if verbose:
                    print(f"  削除: {csv_file.name}")
            else:
                if verbose:
                    print(f"  ⚠️  CSVファイルが見つかりません: {csv_file}")
                success = False
        
        return success
        
    except PermissionError as e:
        raise CleanupError(f"ファイル削除権限がありません: {str(e)}")
    except Exception as e:
        raise CleanupError(f"クリーンアップ中にエラーが発生しました: {str(e)}")


def cleanup_directory(directory: Path, pattern: str = "*", verbose: bool = False) -> int:
    """
    指定ディレクトリ内のファイルを削除
    
    Args:
        directory: クリーンアップするディレクトリ
        pattern: 削除するファイルのパターン（デフォルト: 全ファイル）
        verbose: 詳細ログを出力するか
        
    Returns:
        削除されたファイル数
        
    Raises:
        CleanupError: クリーンアップに失敗した場合
    """
    if not directory.exists():
        if verbose:
            print(f"⚠️  ディレクトリが存在しません: {directory}")
        return 0
    
    try:
        files = list(directory.glob(pattern))
        deleted_count = 0
        
        for file_path in files:
            if file_path.is_file():
                file_path.unlink()
                deleted_count += 1
                if verbose:
                    print(f"  削除: {file_path.name}")
        
        if verbose and deleted_count > 0:
            print(f"✅ {deleted_count}個のファイルを削除しました")
        
        return deleted_count
        
    except PermissionError as e:
        raise CleanupError(f"ファイル削除権限がありません: {str(e)}")
    except Exception as e:
        raise CleanupError(f"クリーンアップ中にエラーが発生しました: {str(e)}")


def main():
    """
    スタンドアロン実行用のメイン関数
    """
    # デフォルトパス設定
    project_root = Path(__file__).parent.parent
    temp_dir = project_root / "temp_extracted"
    filtered_dir = project_root / "filtered_logs"
    
    print("=" * 60)
    print("Juniper Syslog Filter - クリーンアップモジュール")
    print("=" * 60)
    
    try:
        print("\n一時ファイルをクリーンアップ中...")
        
        # temp_extracted/ をクリーンアップ
        temp_count = cleanup_directory(temp_dir, "*.csv", verbose=True)
        
        # filtered_logs/ をクリーンアップ
        filtered_count = cleanup_directory(filtered_dir, "*.csv", verbose=True)
        
        total = temp_count + filtered_count
        
        if total > 0:
            print(f"\n✅ 処理完了: {total}個のファイルを削除しました")
        else:
            print("\n⚠️  削除するファイルがありませんでした")
            
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())