"""
Juniper Syslog Filter - GUI版（Streamlit）

実行方法:
    streamlit run run_gui.py
"""

import streamlit as st
from pathlib import Path
import sys

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# モジュールのインポート
from modules.extract import extract_zip
from modules.filter_keyword import filter_keyword
from modules.cleanup_temp import cleanup_processed_files
from modules.merge_files import merge_csv_files
from modules.reduce_columns import reduce_columns
from modules.extract_routing import extract_routing
from modules.split_ip import split_ip
from modules.classify_ip import classify_ip
from modules.extract_protocol import extract_protocol
from modules.extract_severity_level import extract_severity_level
from modules.extract_severity import extract_severity
from modules.filter_critical_and_merge import filter_and_merge_critical
from modules.export_excel import export_to_excel
from modules.cleanup_all import cleanup_all_directories


def main():
    """
    Streamlit GUI メイン関数
    """
    st.set_page_config(
        page_title="Juniper Syslog Filter", page_icon="🔥", layout="wide"
    )

    st.title("🔥 Juniper Syslog Filter")
    st.markdown("---")

    # サイドバー設定
    with st.sidebar:
        st.header("⚙️ 設定")

        # キーワード設定
        keyword = st.text_input(
            "フィルタキーワード",
            value="RT_IDP_ATTACK",
            help="ログから抽出するキーワードを指定",
        )

        # Severityフィルタ
        severity_filter = st.selectbox(
            "Severityフィルタ",
            options=["CRITICAL", "WARNING", "INFO"],
            index=0,
            help="抽出するSeverityレベルを選択",
        )

        st.markdown("---")

        # 実行ボタン
        run_button = st.button("🚀 実行", type="primary", use_container_width=True)

    # メインエリア
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📊 処理ステータス")
        status_placeholder = st.empty()

    with col2:
        st.subheader("📈 統計情報")
        stats_placeholder = st.empty()

    # 実行処理
    if run_button:
        try:
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

            with st.spinner("処理中..."):
                # 統計情報
                stats = {"処理済みZIP": 0, "フィルタ行数": 0, "最終出力行数": 0}

                # Phase 1: ループ処理
                status_placeholder.info("🔄 Phase 1: ZIP展開 + フィルタリング")

                processed_count = 0
                total_filtered = 0

                while True:
                    zip_files = sorted(source_dir.glob("*.zip"))
                    if not zip_files:
                        break

                    current_zip = zip_files[0]
                    extracted_csvs = extract_zip(current_zip, temp_dir)
                    filtered_count = filter_keyword(
                        extracted_csvs, filtered_dir, keyword=keyword
                    )
                    cleanup_processed_files(current_zip, extracted_csvs, verbose=False)

                    processed_count += 1
                    total_filtered += filtered_count

                    # 統計更新
                    stats["処理済みZIP"] = processed_count
                    stats["フィルタ行数"] = total_filtered
                    stats_placeholder.json(stats)

                # Phase 2: マージ
                status_placeholder.info("🔄 Phase 2: マージ処理")
                filtered_files = sorted(filtered_dir.glob("*.csv"))
                if filtered_files:
                    merged_files = merge_csv_files(
                        filtered_files, merged_dir, max_rows=800000, verbose=False
                    )

                # Phase 3-11: 変換処理（簡略表示）
                status_placeholder.info("🔄 Phase 3-11: データ変換処理")

                # 列削除
                merged_files = sorted(merged_dir.glob("*.csv"))
                if merged_files:
                    reduced_files = reduce_columns(
                        merged_files,
                        reduced_dir,
                        keep_columns=[0, 1, 2, 6],
                        verbose=False,
                    )

                # routing抽出
                reduced_files = sorted(reduced_dir.glob("*.csv"))
                if reduced_files:
                    routed_files = extract_routing(
                        reduced_files, routed_dir, verbose=False
                    )

                # IP分割
                routed_files = sorted(routed_dir.glob("*.csv"))
                if routed_files:
                    splitted_files = split_ip(routed_files, splitted_dir, verbose=False)

                # IP分類
                splitted_files = sorted(splitted_dir.glob("*.csv"))
                if splitted_files:
                    classified_files = classify_ip(
                        splitted_files, classified_dir, verbose=False
                    )

                # protocol抽出
                classified_files = sorted(classified_dir.glob("*.csv"))
                if classified_files:
                    protocol_files = extract_protocol(
                        classified_files, protocol_dir, verbose=False
                    )

                # SeverityLevel抽出
                protocol_files = sorted(protocol_dir.glob("*.csv"))
                if protocol_files:
                    severity_level_files = extract_severity_level(
                        protocol_files, severity_dir, verbose=False
                    )

                # Severity抽出
                severity_level_files = sorted(severity_dir.glob("*.csv"))
                if severity_level_files:
                    severity_extracted_files = extract_severity(
                        severity_level_files, severity_extracted_dir, verbose=False
                    )

                # Phase 10: CRITICAL抽出 + マージ
                status_placeholder.info(f"🔄 Phase 10: {severity_filter}抽出 + マージ")
                severity_extracted_files = sorted(severity_extracted_dir.glob("*.csv"))
                if severity_extracted_files:
                    critical_output = critical_dir / "critical_merged.csv"
                    result = filter_and_merge_critical(
                        severity_extracted_files,
                        critical_output,
                        severity_filter=severity_filter,
                        verbose=False,
                    )

                    if result:
                        # 最終行数をカウント
                        import pandas as pd

                        df = pd.read_csv(result)
                        stats["最終出力行数"] = len(df)
                        stats_placeholder.json(stats)

                # Phase 11: Excel出力
                status_placeholder.info("🔄 Phase 11: Excel出力")
                critical_file = critical_dir / "critical_merged.csv"
                if critical_file.exists():
                    excel_output = export_to_excel(
                        critical_file, final_output_dir, verbose=False
                    )

                # Phase 12: クリーンアップ
                status_placeholder.info("🔄 Phase 12: クリーンアップ")
                cleanup_all_directories(project_root, verbose=False)

                # 完了
                status_placeholder.success(f"✅ 処理完了！出力: {excel_output.name}")
                st.balloons()

        except Exception as e:
            status_placeholder.error(f"❌ エラーが発生しました: {str(e)}")
            st.exception(e)

    else:
        # 初期状態
        status_placeholder.info("⏸️ 設定を確認して「実行」ボタンをクリックしてください")

        # 説明
        st.markdown("### 📝 使い方")
        st.markdown(
            """
        1. **source_logs/** ディレクトリにZIPファイルを配置
        2. サイドバーで設定を確認
        3. 「実行」ボタンをクリック
        4. 処理完了後、**final_output/** にExcelファイルが出力されます
        """
        )

        st.markdown("### 📋 現在の設定")
        st.code(
            f"""
キーワード: {keyword}
Severityフィルタ: {severity_filter}
        """
        )


if __name__ == "__main__":
    main()
