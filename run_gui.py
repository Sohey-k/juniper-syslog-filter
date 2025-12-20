"""
Juniper Syslog Filter - GUI版（Streamlit - ハイブリッド版 Final）

パラメータ変更可能 + リアルタイム進捗表示 + 経過時間表示
- CLI並みの速度（subprocess経由）
- GUI上でキーワード・Severity変更可能
- リアルタイム進捗表示
- 経過時間表示

実行方法:
    streamlit run run_gui.py
"""

import streamlit as st
from pathlib import Path
import subprocess
import sys
import threading
import time
import os  # ← 追加

# プロジェクトルート
project_root = Path(__file__).parent


def main():
    """
    Streamlit GUI メイン関数（ハイブリッド版 Final）
    """
    st.set_page_config(
        page_title="Juniper Syslog Filter", page_icon="🔥", layout="wide"
    )

    st.title("🔥 Juniper Syslog Filter")
    st.markdown("---")

    # セッションステートの初期化
    if "process" not in st.session_state:
        st.session_state.process = None
    if "is_running" not in st.session_state:
        st.session_state.is_running = False

    # サイドバー設定
    with st.sidebar:
        st.header("⚙️ 設定")

        # キーワード設定
        keyword = st.text_input(
            "フィルタキーワード",
            value="RT_IDP_ATTACK",
            help="ログから抽出するキーワードを指定",
            disabled=st.session_state.is_running,
        )

        # Severityフィルタ
        severity_filter = st.selectbox(
            "Severityフィルタ",
            options=["CRITICAL", "WARNING", "INFO"],
            index=0,
            help="抽出するSeverityレベルを選択",
            disabled=st.session_state.is_running,
        )

        st.markdown("---")

        st.info("💡 リアルタイム進捗表示（処理速度はCLI版が高速です）")

        # 実行ボタンのみ
        run_button = st.button(
            "🚀 実行",
            type="primary",
            use_container_width=True,
            disabled=st.session_state.is_running,
        )

    # メインエリア
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📊 処理ステータス")
        status_placeholder = st.empty()

        st.subheader("📝 処理ログ")
        log_placeholder = st.empty()

    with col2:
        st.subheader("📋 設定確認")
        st.code(
            f"""
キーワード: {keyword}
Severity: {severity_filter}
        """
        )

    # 実行処理
    if run_button:
        try:
            # 処理開始
            st.session_state.is_running = True
            status_placeholder.info("🔄 処理開始...")

            # ログを格納するリスト
            log_lines = []

            # 環境変数でバッファリングを完全無効化
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"

            # サブプロセスで実行（リアルタイム出力）
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-u",  # バッファリング無効化
                    "run_with_args.py",
                    "--keyword",
                    keyword,
                    "--severity",
                    severity_filter,
                ],
                cwd=str(project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,  # 行バッファリング
                env=env,  # ← 環境変数を設定
            )

            # セッションステートに保存
            st.session_state.process = process

            # 出力をリアルタイムで読み取り
            status_placeholder.info("🔄 ETLパイプライン実行中...")

            # 処理開始時刻を記録
            start_time = time.time()

            try:
                for line in iter(process.stdout.readline, ""):
                    if line:
                        log_lines.append(line.rstrip())

                        # 経過時間を計算
                        elapsed = time.time() - start_time
                        elapsed_min = int(elapsed // 60)
                        elapsed_sec = int(elapsed % 60)

                        # 最新50行をログ表示（スクロール対策）
                        display_lines = log_lines[-50:]

                        # codeブロックで表示（text_areaより更新が確実）
                        log_placeholder.code("\n".join(display_lines), language=None)

                        # Phase完了を検出してステータス更新（経過時間付き）
                        if "[OK] Phase" in line:
                            phase_num = line.split("Phase")[1].strip().split()[0]
                            status_placeholder.info(
                                f"🔄 Phase {phase_num} 完了... ⏱️ 経過時間: {elapsed_min}分{elapsed_sec}秒"
                            )
                        else:
                            # Phase完了以外の行でも定期的に経過時間を更新
                            status_placeholder.info(
                                f"🔄 ETLパイプライン実行中... ⏱️ 経過時間: {elapsed_min}分{elapsed_sec}秒"
                            )

                        # Streamlitの更新を確実にするため、わずかに待機
                        time.sleep(0.01)

                # プロセス終了待機
                process.stdout.close()
                return_code = process.wait()

                # 合計実行時間を計算
                total_time = time.time() - start_time
                total_min = int(total_time // 60)
                total_sec = int(total_time % 60)

            except Exception as e:
                # エラーが発生した場合
                status_placeholder.error(f"❌ 実行中にエラーが発生しました")
                st.exception(e)
                st.session_state.is_running = False
                st.session_state.process = None
                return

            # 結果判定
            if return_code == 0:
                status_placeholder.success(
                    f"✅ 処理完了！⏱️ 合計実行時間: {total_min}分{total_sec}秒"
                )
                st.balloons()

                # 出力ファイル確認
                final_output_dir = project_root / "final_output"
                excel_files = list(final_output_dir.glob("*.xlsx"))

                if excel_files:
                    st.success(f"📊 {len(excel_files)}個のExcelファイルを出力しました")

                    # ファイル一覧表示
                    with st.expander("📁 出力ファイル一覧", expanded=True):
                        for excel_file in sorted(excel_files):
                            st.write(f"✅ {excel_file.name}")
                else:
                    st.warning(
                        "⚠️ 出力ファイルがありません（フィルタ条件に一致する行がなかった可能性があります）"
                    )

                # 完全なログを表示
                with st.expander("📝 完全なログ"):
                    st.text("\n".join(log_lines))

            else:
                status_placeholder.error(
                    f"❌ エラーが発生しました（終了コード: {return_code}）"
                )

                # エラーログ表示
                st.error("エラー詳細:")
                st.text("\n".join(log_lines))

            # 処理完了後、状態をリセット
            st.session_state.is_running = False
            st.session_state.process = None

        except Exception as e:
            status_placeholder.error(f"❌ 実行エラー: {str(e)}")
            st.exception(e)
            st.session_state.is_running = False
            st.session_state.process = None

    else:
        # 初期状態（実行されていない場合）
        if not st.session_state.is_running:
            status_placeholder.info(
                "⏸️ 設定を確認して「実行」ボタンをクリックしてください"
            )

            # 説明
            st.markdown("### 📝 使い方")
            st.markdown(
                """
            1. **source_logs/** ディレクトリにZIPファイルを配置
            2. サイドバーで設定を確認（必要に応じて変更）
            3. 「実行」ボタンをクリック
            4. リアルタイムで処理ログと経過時間を確認
            5. 約13分で完了
            6. 処理完了後、**final_output/** にExcelファイルが出力されます
            """
            )

            st.markdown("### ⚡ ハイブリッド版の特徴")

            col_a, col_b = st.columns(2)

            with col_a:
                st.markdown("**✅ できること**")
                st.markdown(
                    """
                - GUI上でキーワード変更
                - GUI上でSeverity変更
                - **リアルタイム進捗表示** ✨
                - **経過時間表示** ⏱️
                - Phase別の進捗確認
                - 実行ログの確認
                - 出力ファイル一覧の表示
                
                ⚠️ **処理速度について**: CLIの方が高速です。速さを求める場合はCLI版をお勧めします。
                """
                )

            with col_b:
                st.markdown("**⏱️ 経過時間について**")
                st.markdown(
                    """
                - リアルタイムで経過時間を表示
                - Phase完了ごとに更新
                - 完了時に合計時間を表示
                - 処理の進捗が一目でわかる
                """
                )

            st.markdown("### 📊 バージョン比較")
            comparison_data = {
                "バージョン": ["通常GUI", "v1", "v2", "**v3 Final**"],
                "速度": ["13分", "13分", "13分", "**13分**"],
                "進捗表示": ["詳細", "なし", "リアルタイム", "**リアルタイム**"],
                "経過時間": ["なし", "なし", "なし", "**あり** ⏱️"],
            }
            st.table(comparison_data)


if __name__ == "__main__":
    main()
