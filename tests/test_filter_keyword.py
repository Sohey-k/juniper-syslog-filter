"""
test_filter_keyword.py - filter_keyword.pyのテストコード

キーワードフィルタリング機能（pandas + ファイル出力版）をテスト
"""

import pytest
import pandas as pd
import csv
from pathlib import Path
from modules.filter_keyword import filter_keyword, FilterError


@pytest.fixture
def temp_dir(tmp_path):
    """一時ディレクトリのフィクスチャ"""
    return tmp_path


def create_test_csv(csv_path: Path, rows: list):
    """テスト用CSVファイルを作成"""
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "Timestamp",
                "Hostname",
                "AppName",
                "SeverityLevel",
                "Severity",
                "LogType",
                "Message",
            ]
        )
        writer.writerows(rows)


class TestFilterKeyword:
    """filter_keyword関数のテスト"""

    def test_filter_with_matching_rows(self, temp_dir):
        """正常系: キーワードを含む行のみフィルタリング"""
        # テストデータ作成
        rows = [
            [
                "2025-12-16T00:00:00Z",
                "srx-fw01",
                "RT_IDP",
                2,
                "CRITICAL",
                "THREAT",
                "RT_IDP_ATTACK_LOG: SQL injection detected",
            ],
            [
                "2025-12-16T00:01:00Z",
                "srx-fw01",
                "RT_FLOW",
                6,
                "INFO",
                "NORMAL",
                "RT_FLOW_SESSION_CREATE: session created",
            ],
            [
                "2025-12-16T00:02:00Z",
                "srx-fw01",
                "RT_IDP",
                2,
                "CRITICAL",
                "THREAT",
                "RT_IDP_ATTACK_LOG: Port scan detected",
            ],
        ]

        input_path = temp_dir / "test.csv"
        output_dir = temp_dir / "output"
        create_test_csv(input_path, rows)

        # 実行
        count = filter_keyword([input_path], output_dir, keyword="RT_IDP_ATTACK")

        # 検証: 2行が抽出される
        assert count == 2

        # 出力ファイルの内容を検証
        output_files = list(output_dir.glob("*.csv"))
        assert len(output_files) == 1

        df = pd.read_csv(output_files[0])
        assert len(df) == 2
        assert all(df["Message"].str.contains("RT_IDP_ATTACK"))

    def test_filter_with_no_matching_rows(self, temp_dir):
        """正常系: キーワード不一致の場合はファイルを出力しない"""
        rows = [
            [
                "2025-12-16T00:00:00Z",
                "srx-fw01",
                "RT_FLOW",
                6,
                "INFO",
                "NORMAL",
                "RT_FLOW_SESSION_CREATE: session created",
            ],
        ]

        input_path = temp_dir / "test.csv"
        output_dir = temp_dir / "output"
        create_test_csv(input_path, rows)

        # 実行
        count = filter_keyword([input_path], output_dir, keyword="RT_IDP_ATTACK")

        # 検証: 0行、ファイルも出力されない
        assert count == 0
        assert len(list(output_dir.glob("*.csv"))) == 0

    def test_filter_multiple_files(self, temp_dir):
        """正常系: 複数ファイルの処理"""
        rows1 = [
            [
                "2025-12-16T00:00:00Z",
                "srx-fw01",
                "RT_IDP",
                2,
                "CRITICAL",
                "THREAT",
                "RT_IDP_ATTACK_LOG: SQL injection detected",
            ]
        ]
        rows2 = [
            [
                "2025-12-16T01:00:00Z",
                "srx-fw01",
                "RT_IDP",
                2,
                "CRITICAL",
                "THREAT",
                "RT_IDP_ATTACK_LOG: Port scan detected",
            ]
        ]

        input_path1 = temp_dir / "test1.csv"
        input_path2 = temp_dir / "test2.csv"
        output_dir = temp_dir / "output"

        create_test_csv(input_path1, rows1)
        create_test_csv(input_path2, rows2)

        # 実行
        count = filter_keyword(
            [input_path1, input_path2], output_dir, keyword="RT_IDP_ATTACK"
        )

        # 検証: 2ファイルから合計2行
        assert count == 2
        assert len(list(output_dir.glob("*.csv"))) == 2

    def test_filter_missing_message_column(self, temp_dir):
        """異常系: Message列が存在しない場合はエラー"""
        # Message列がないCSVを作成
        csv_path = temp_dir / "test.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Hostname"])
            writer.writerow(["2025-12-16T00:00:00Z", "srx-fw01"])

        output_dir = temp_dir / "output"

        # 実行 & 検証
        with pytest.raises(FilterError, match="Message列が見つかりません"):
            filter_keyword([csv_path], output_dir)
