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
from modules.cleanup_temp import cleanup_processed_files, cleanup_directory
from modules.merge_files import merge_csv_files
from modules.reduce_columns import reduce_columns
from modules.extract_routing import extract_routing
from modules.split_ip import split_ip
from modules.classify_ip import classify_ip


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
    merged_dir = project_root / "merged_logs"  # ← どこからでも見える
    reduced_dir = project_root / "reduced_logs"
    routed_dir = project_root / "routed_logs"
    splitted_dir = project_root / "splitted_logs"
    classified_dir = project_root / "classified_logs"

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
            filtered_count = filter_keyword(
                extracted_csvs, filtered_dir, keyword="RT_IDP_ATTACK"
            )
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

        # Phase 2: マージ処理
        print("\n[Phase 2] マージ処理開始")
        print("-" * 70)

        # filtered_logs/ の全CSVをマージ
        filtered_files = sorted(filtered_dir.glob("*.csv"))

        if not filtered_files:
            print("\n⚠️  マージするファイルがありません")
        else:
            merged_dir = project_root / "merged_logs"
            print(f"📄 対象ファイル数: {len(filtered_files)}")
            print(f"📦 マージ中...", end=" ")

            merged_files = merge_csv_files(
                filtered_files, merged_dir, max_rows=800000, verbose=False
            )

            print(f"✓ ({len(merged_files)}ファイル作成)")

            print("\n" + "=" * 70)
            print("✅ Phase 2 完了")
            print("=" * 70)

        # filtered_logs/ 内の全CSVを削除
        print(f"  └─ クリーンアップ中...", end=" ")
        cleanup_directory(filtered_dir, "*.csv", verbose=False)
        print("✓")

        # merged_logs/ の全CSVから不要列を削除
        merged_files = sorted(merged_dir.glob("*.csv"))

        if not merged_files:
            print("\n⚠️  処理するファイルがありません")
        else:
            reduced_dir = project_root / "reduced_logs"
            print(f"📄 対象ファイル数: {len(merged_files)}")
            print(f"保持する列: [0, 1, 2, 6] (Timestamp, Hostname, AppName, Message)")
            print(f"🔧 列削減中...", end=" ")

            reduced_files = reduce_columns(
                merged_files, reduced_dir, keep_columns=[0, 1, 2, 6], verbose=False
            )

            print(f"✓ ({len(reduced_files)}ファイル作成)")

            print("\n" + "=" * 70)
            print("✅ Phase 3 完了")
            print("=" * 70)

        # merged_dir/ 内の全CSVを削除
        print(f"  └─ クリーンアップ中...", end=" ")
        cleanup_directory(merged_dir, "*.csv", verbose=False)
        print("✓")

        # Phase 4: routing抽出処理
        print("\n[Phase 4] routing抽出処理開始")
        print("-" * 70)

        # reduced_logs/ の全CSVからrouting列を抽出
        reduced_files = sorted(reduced_dir.glob("*.csv"))

        if not reduced_files:
            print("\n⚠️  処理するファイルがありません")
        else:
            print(f"📄 対象ファイル数: {len(reduced_files)}")
            print(f"抽出パターン: srcIP/port > dstIP/port → srcIP > dstIP")
            print(f"🔍 routing抽出中...", end=" ")

            routed_files = extract_routing(reduced_files, routed_dir, verbose=False)

            print(f"✓ ({len(routed_files)}ファイル作成)")

            print("\n" + "=" * 70)
            print("✅ Phase 4 完了")
            print("=" * 70)

        # reduced_dir/ 内の全CSVを削除
        print(f"  └─ クリーンアップ中...", end=" ")
        cleanup_directory(reduced_dir, "*.csv", verbose=False)
        print("✓")

        # Phase 5: IP分割処理
        print("\n[Phase 5] IP分割処理開始")
        print("-" * 70)

        # routed_logs/ の全CSVからrouting列を分割
        routed_files = sorted(routed_dir.glob("*.csv"))

        if not routed_files:
            print("\n⚠️  処理するファイルがありません")
        else:
            print(f"📄 対象ファイル数: {len(routed_files)}")
            print(f"分割パターン: routing → srcIP, dstIP")
            print(f"✂️  IP分割中...", end=" ")

            splitted_files = split_ip(routed_files, splitted_dir, verbose=False)

            print(f"✓ ({len(splitted_files)}ファイル作成)")

            print("\n" + "=" * 70)
            print("✅ Phase 5 完了")
            print("=" * 70)

        # routed_dir/ 内の全CSVを削除
        print(f"  └─ クリーンアップ中...", end=" ")
        cleanup_directory(routed_dir, "*.csv", verbose=False)
        print("✓")

        # Phase 6: IP分類処理
        print("\n[Phase 6] IP分類処理開始")
        print("-" * 70)

        # splitted_logs/ の全CSVからIPアドレスを分類
        splitted_files = sorted(splitted_dir.glob("*.csv"))

        if not splitted_files:
            print("\n⚠️  処理するファイルがありません")
        else:
            print(f"📄 対象ファイル数: {len(splitted_files)}")
            print(f"分類: private (10.x, 172.16-31.x, 192.168.x) / global")
            print(f"🏷️  IP分類中...", end=" ")

            classified_files = classify_ip(
                splitted_files, classified_dir, verbose=False
            )

            print(f"✓ ({len(classified_files)}ファイル作成)")

            print("\n" + "=" * 70)
            print("✅ Phase 6 完了")
            print("=" * 70)

        # splitted_dir/ 内の全CSVを削除
        print(f"  └─ クリーンアップ中...", end=" ")
        cleanup_directory(splitted_dir, "*.csv", verbose=False)
        print("✓")

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
