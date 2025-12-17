"""
Juniper Syslog Filter - Main Entry Point

ETLパイプラインの統合実行
"""

from pathlib import Path
import sys

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# モジュールのインポート
from modules.extract import extract_zip
from modules.filter_keyword import filter_keyword
from modules.cleanup_temp import cleanup_processed_files


def main():
    """
    メイン処理
    """
    print("=" * 70)
    print("Juniper Syslog Filter - Starting...")
    print("=" * 70)
    
    # ディレクトリパス設定
    source_dir = project_root / "source_logs"
    temp_dir = project_root / "temp_extracted"
    filtered_dir = project_root / "filtered_logs"
    
    try:
        # Phase 1: ループ処理（ZIPファイルが無くなるまで）
        print("\n[Phase 1] ループ処理開始")
        print("-" * 70)
        
        processed_count = 0
        
        while True:
            # 1. source_logs/ から ZIP を1つ取得
            zip_files = sorted(source_dir.glob("*.zip"))
            
            if not zip_files:
                print("\n✅ 全てのZIPファイルを処理しました")
                break
            
            current_zip = zip_files[0]
            print(f"\n📦 処理中: {current_zip.name}")
            
            # 2. ZIP展開
            print(f"  ├─ 展開中...", end=" ")
            extracted_csvs = extract_zip(current_zip, temp_dir)
            print(f"✓ ({len(extracted_csvs)}ファイル)")
            
            # 3. キーワードフィルタリング
            print(f"  ├─ フィルタリング中...", end=" ")
            filtered_count = filter_keyword(extracted_csvs, filtered_dir, keyword="RT_IDP_ATTACK")
            print(f"✓ ({filtered_count}行)")
            
            # 4. クリーンアップ（処理済みZIPと一時CSVを削除）
            print(f"  └─ クリーンアップ中...", end=" ")
            cleanup_processed_files(current_zip, extracted_csvs, verbose=False)
            print("✓")
            
            processed_count += 1
        
        if processed_count == 0:
            print("\n⚠️  処理するZIPファイルがありませんでした")
        else:
            print(f"\n✅ {processed_count}個のZIPファイルを処理しました")
        
        print("\n" + "=" * 70)
        print("✅ Phase 1 完了")
        print("=" * 70)
        
    except Exception as e:
        print("\n" + "=" * 70)
        print(f"❌ エラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()
        print("=" * 70)
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())