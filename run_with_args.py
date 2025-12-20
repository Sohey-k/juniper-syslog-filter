"""
Juniper Syslog Filter - Main Entry Point

ETLパイプラインの統合実行
コマンドライン引数対応版（絵文字なし・Windows対応）
"""

from pathlib import Path
import sys
import argparse

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
from modules.extract_protocol import extract_protocol
from modules.extract_severity_level import extract_severity_level
from modules.extract_severity import extract_severity
from modules.filter_critical import filter_critical
from modules.export_excel import export_to_excel
from modules.cleanup_all import cleanup_all_directories


def main():
    """
    メイン処理
    """
    # コマンドライン引数のパース
    parser = argparse.ArgumentParser(description="Juniper Syslog Filter - ETL Pipeline")
    parser.add_argument(
        "--keyword",
        type=str,
        default="RT_IDP_ATTACK",
        help="Filter keyword (default: RT_IDP_ATTACK)",
    )
    parser.add_argument(
        "--severity",
        type=str,
        default="CRITICAL",
        choices=["CRITICAL", "WARNING", "INFO"],
        help="Severity filter (default: CRITICAL)",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("Juniper Syslog Filter - Starting...")
    print("=" * 70)
    print("[Settings]")
    print(f"   Keyword: {args.keyword}")
    print(f"   Severity: {args.severity}")
    print("=" * 70)

    # ディレクトリパス設定
    source_dir = project_root / "source_logs"
    temp_dir = project_root / "temp_extracted"
    filtered_dir = project_root / "filtered_logs"
    merged_dir = project_root / "merged_logs"
    reduced_dir = project_root / "reduced_logs"
    routed_dir = project_root / "routed_logs"
    splitted_dir = project_root / "splitted_logs"
    classified_dir = project_root / "classified_logs"
    protocol_dir = project_root / "protocol_extracted"
    severity_dir = project_root / "severity_level_extracted"
    severity_extracted_dir = project_root / "severity_extracted"
    critical_dir = project_root / "critical_only"
    final_output_dir = project_root / "final_output"

    try:
        # Phase 1: ループ処理（ZIPファイルが無くなるまで）
        print("\n[Phase 1] Loop processing started")
        print("-" * 70)

        processed_count = 0

        while True:
            # 1. source_logs/ から ZIP を1つ取得
            zip_files = sorted(source_dir.glob("*.zip"))

            if not zip_files:
                print("\n[OK] All ZIP files processed")
                break

            current_zip = zip_files[0]
            print(f"\n[ZIP] Processing: {current_zip.name}")

            # 2. ZIP展開
            print(f"  |- Extracting...", end=" ")
            extracted_csvs = extract_zip(current_zip, temp_dir)
            print(f"OK ({len(extracted_csvs)} files)")

            # 3. キーワードフィルタリング（引数から取得）
            print(f"  |- Filtering...", end=" ")
            filtered_count = filter_keyword(
                extracted_csvs, filtered_dir, keyword=args.keyword
            )
            print(f"OK ({filtered_count} rows)")

            # 4. クリーンアップ（処理済みZIPと一時CSVを削除）
            print(f"  +- Cleanup...", end=" ")
            cleanup_processed_files(current_zip, extracted_csvs, verbose=False)
            print("OK")

            processed_count += 1

        if processed_count == 0:
            print("\n[Warning] No ZIP files to process")
        else:
            print(f"\n[OK] Processed {processed_count} ZIP files")

        print("\n" + "=" * 70)
        print("[OK] Phase 1 completed")
        print("=" * 70)

        # Phase 2: マージ処理
        print("\n[Phase 2] Merge processing started")
        print("-" * 70)

        filtered_files = sorted(filtered_dir.glob("*.csv"))

        if not filtered_files:
            print("\n[Warning] No files to merge")
        else:
            print(f"[Files] Target: {len(filtered_files)}")
            print(f"[Merge] Processing...", end=" ")

            merged_files = merge_csv_files(
                filtered_files, merged_dir, max_rows=800000, verbose=False
            )

            print(f"OK ({len(merged_files)} files created)")

            print("\n" + "=" * 70)
            print("[OK] Phase 2 completed")
            print("=" * 70)

        print(f"  +- Cleanup...", end=" ")
        cleanup_directory(filtered_dir, "*.csv", verbose=False)
        print("OK")

        # Phase 3: 列削減処理
        print("\n[Phase 3] Column reduction started")
        print("-" * 70)

        merged_files = sorted(merged_dir.glob("*.csv"))

        if not merged_files:
            print("\n[Warning] No files to process")
        else:
            print(f"[Files] Target: {len(merged_files)}")
            print(f"Keep columns: [0, 1, 2, 6] (Timestamp, Hostname, AppName, Message)")
            print(f"[Change] Processing...", end=" ")

            reduced_files = reduce_columns(
                merged_files, reduced_dir, keep_columns=[0, 1, 2, 6], verbose=False
            )

            print(f"OK ({len(reduced_files)} files created)")

            print("\n" + "=" * 70)
            print("[OK] Phase 3 completed")
            print("=" * 70)

        print(f"  +- Cleanup...", end=" ")
        cleanup_directory(merged_dir, "*.csv", verbose=False)
        print("OK")

        # Phase 4: routing抽出処理
        print("\n[Phase 4] Routing extraction started")
        print("-" * 70)

        reduced_files = sorted(reduced_dir.glob("*.csv"))

        if not reduced_files:
            print("\n[Warning] No files to process")
        else:
            print(f"[Files] Target: {len(reduced_files)}")
            print(f"Extract pattern: srcIP/port > dstIP/port -> srcIP > dstIP")
            print(f"[Extract] Processing...", end=" ")

            routed_files = extract_routing(reduced_files, routed_dir, verbose=False)

            print(f"OK ({len(routed_files)} files created)")

            print("\n" + "=" * 70)
            print("[OK] Phase 4 completed")
            print("=" * 70)

        print(f"  +- Cleanup...", end=" ")
        cleanup_directory(reduced_dir, "*.csv", verbose=False)
        print("OK")

        # Phase 5: IP分割処理
        print("\n[Phase 5] IP split started")
        print("-" * 70)

        routed_files = sorted(routed_dir.glob("*.csv"))

        if not routed_files:
            print("\n[Warning] No files to process")
        else:
            print(f"[Files] Target: {len(routed_files)}")
            print(f"Split pattern: routing -> srcIP, dstIP")
            print(f"[Split] Processing...", end=" ")

            splitted_files = split_ip(routed_files, splitted_dir, verbose=False)

            print(f"OK ({len(splitted_files)} files created)")

            print("\n" + "=" * 70)
            print("[OK] Phase 5 completed")
            print("=" * 70)

        print(f"  +- Cleanup...", end=" ")
        cleanup_directory(routed_dir, "*.csv", verbose=False)
        print("OK")

        # Phase 6: IP分類処理
        print("\n[Phase 6] IP classification started")
        print("-" * 70)

        splitted_files = sorted(splitted_dir.glob("*.csv"))

        if not splitted_files:
            print("\n[Warning] No files to process")
        else:
            print(f"[Files] Target: {len(splitted_files)}")
            print(f"Classification: private (10.x, 172.16-31.x, 192.168.x) / global")
            print(f"[Classify] Processing...", end=" ")

            classified_files = classify_ip(
                splitted_files, classified_dir, verbose=False
            )

            print(f"OK ({len(classified_files)} files created)")

            print("\n" + "=" * 70)
            print("[OK] Phase 6 completed")
            print("=" * 70)

        print(f"  +- Cleanup...", end=" ")
        cleanup_directory(splitted_dir, "*.csv", verbose=False)
        print("OK")

        # Phase 7: protocol抽出処理
        print("\n[Phase 7] Protocol extraction started")
        print("-" * 70)

        classified_files = sorted(classified_dir.glob("*.csv"))

        if not classified_files:
            print("\n[Warning] No files to process")
        else:
            print(f"[Files] Target: {len(classified_files)}")
            print(f"Extract pattern: protocol=xxx")
            print(f"[Extract] Processing...", end=" ")

            protocol_files = extract_protocol(
                classified_files, protocol_dir, verbose=False
            )

            print(f"OK ({len(protocol_files)} files created)")

            print("\n" + "=" * 70)
            print("[OK] Phase 7 completed")
            print("=" * 70)

        print(f"  +- Cleanup...", end=" ")
        cleanup_directory(classified_dir, "*.csv", verbose=False)
        print("OK")

        # Phase 8: SeverityLevel抽出処理
        print("\n[Phase 8] SeverityLevel extraction started")
        print("-" * 70)

        protocol_files = sorted(protocol_dir.glob("*.csv"))

        if not protocol_files:
            print("\n[Warning] No files to process")
        else:
            print(f"[Files] Target: {len(protocol_files)}")
            print(f"Extract pattern: SeverityLevel=number")
            print(f"[Extract] Processing...", end=" ")

            severity_files = extract_severity_level(
                protocol_files, severity_dir, verbose=False
            )

            print(f"OK ({len(severity_files)} files created)")

            print("\n" + "=" * 70)
            print("[OK] Phase 8 completed")
            print("=" * 70)

        print(f"  +- Cleanup...", end=" ")
        cleanup_directory(protocol_dir, "*.csv", verbose=False)
        print("OK")

        # Phase 9: Severity抽出処理
        print("\n[Phase 9] Severity extraction started")
        print("-" * 70)

        severity_level_files = sorted(severity_dir.glob("*.csv"))

        if not severity_level_files:
            print("\n[Warning] No files to process")
        else:
            print(f"[Files] Target: {len(severity_level_files)}")
            print(f"Extract pattern: Severity=xxx")
            print(f"[Extract] Processing...", end=" ")

            severity_extracted_files = extract_severity(
                severity_level_files, severity_extracted_dir, verbose=False
            )

            print(f"OK ({len(severity_extracted_files)} files created)")

            print("\n" + "=" * 70)
            print("[OK] Phase 9 completed")
            print("=" * 70)

        print(f"  +- Cleanup...", end=" ")
        cleanup_directory(severity_dir, "*.csv", verbose=False)
        print("OK")

        # Phase 10: CRITICAL抽出処理（引数から取得）
        print(f"\n[Phase 10] {args.severity} extraction started")
        print("-" * 70)

        severity_extracted_files = sorted(severity_extracted_dir.glob("*.csv"))

        if not severity_extracted_files:
            print("\n[Warning] No files to process")
        else:
            print(f"[Files] Target: {len(severity_extracted_files)}")
            print(f"Filter condition: Severity={args.severity}")
            print(f"[Extract] {args.severity} filtering...", end=" ")

            critical_files = filter_critical(
                severity_extracted_files,
                critical_dir,
                severity_filter=args.severity,
                verbose=False,
            )

            if critical_files:
                print(f"OK ({len(critical_files)} files)")
            else:
                print(f"[Warning] No {args.severity} rows found")

            print("\n" + "=" * 70)
            print("[OK] Phase 10 completed")
            print("=" * 70)

        print(f"  +- Cleanup...", end=" ")
        cleanup_directory(severity_extracted_dir, "*.csv", verbose=False)
        print("OK")

        # Phase 11: Excel最終出力処理
        print("\n[Phase 11] Excel output started")
        print("-" * 70)

        critical_files = sorted(critical_dir.glob("*.csv"))

        if not critical_files:
            print("\n[Warning] No critical files found")
        else:
            print(f"[Files] Target: {len(critical_files)}")
            print(f"[Excel] Processing...", end=" ")

            excel_count = 0
            for critical_file in critical_files:
                excel_output = export_to_excel(
                    critical_file, final_output_dir, verbose=False
                )
                excel_count += 1

            print(f"OK ({excel_count} files)")

            print("\n" + "=" * 70)
            print("[OK] Phase 11 completed")
            print("=" * 70)

        # Phase 12: 全ディレクトリクリーンアップ
        print("\n[Phase 12] Directory cleanup started")
        print("-" * 70)
        print("[Delete] Cleaning intermediate directories...", end=" ")

        deleted_count = cleanup_all_directories(project_root, verbose=False)

        print(f"OK ({deleted_count} directories)")

        print("\n" + "=" * 70)
        print("[OK] Phase 12 completed")
        print("=" * 70)

    except Exception as e:
        print("\n" + "=" * 70)
        print(f"[Error] An error occurred: {str(e)}")
        import traceback

        traceback.print_exc()
        print("=" * 70)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
