"""
test_filter_critical_and_merge.py - filter_critical_and_merge.pyのテストコード

CRITICAL抽出 + マージ機能（pandas + ファイル出力版）をテスト
"""

import pytest
import pandas as pd
import csv
from pathlib import Path
from modules.filter_critical_and_merge import (
    filter_and_merge_critical,
    FilterCriticalError,
)


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
                "routing",
                "srcIP",
                "srcIP_type",
                "dstIP",
                "dstIP_type",
                "protocol",
                "SeverityLevel",
                "Severity",
                "Message",
            ]
        )
        writer.writerows(rows)


class TestFilterCriticalAndMerge:
    """filter_and_merge_critical関数のテスト"""

    def test_filter_critical_basic(self, temp_dir):
        """正常系: CRITICAL行のみが抽出される"""
        # テストデータ作成（CRITICAL 2行, WARNING 1行）
        rows = [
            [
                "2025-12-16T00:00:00Z",
                "srx-fw01",
                "RT_IDP",
                "192.168.1.5 > 8.8.8.8",
                "192.168.1.5",
                "private",
                "8.8.8.8",
                "global",
                "tcp",
                "2",
                "CRITICAL",
                "RT_IDP_ATTACK_LOG: SQL injection SeverityLevel=2 Severity=CRITICAL",
            ],
            [
                "2025-12-16T00:01:00Z",
                "srx-fw01",
                "RT_IDP",
                "10.0.0.1 > 1.1.1.1",
                "10.0.0.1",
                "private",
                "1.1.1.1",
                "global",
                "udp",
                "4",
                "WARNING",
                "RT_IDP_ATTACK_LOG: Port scan SeverityLevel=4 Severity=WARNING",
            ],
            [
                "2025-12-16T00:02:00Z",
                "srx-fw01",
                "RT_IDP",
                "172.16.0.1 > 8.8.4.4",
                "172.16.0.1",
                "private",
                "8.8.4.4",
                "global",
                "tcp",
                "2",
                "CRITICAL",
                "RT_IDP_ATTACK_LOG: Malware detected SeverityLevel=2 Severity=CRITICAL",
            ],
        ]

        input_path = temp_dir / "test.csv"
        output_file = temp_dir / "critical_merged.csv"
        create_test_csv(input_path, rows)

        # 実行
        result = filter_and_merge_critical([input_path], output_file, verbose=False)

        # 検証: ファイルが作成される
        assert result is not None
        assert result.exists()

        # 出力ファイルの内容を検証
        df = pd.read_csv(result, keep_default_na=False)

        # CRITICAL行のみ（2行）が抽出される
        assert len(df) == 2
        assert all(df["Severity"] == "CRITICAL")

        # WARNING行は除外される
        assert "10.0.0.1" not in df["srcIP"].values

    def test_filter_critical_multiple_files(self, temp_dir):
        """正常系: 複数ファイルが1つにマージされる"""
        rows1 = [
            [
                "2025-12-16T00:00:00Z",
                "srx-fw01",
                "RT_IDP",
                "192.168.1.1 > 8.8.8.8",
                "192.168.1.1",
                "private",
                "8.8.8.8",
                "global",
                "tcp",
                "2",
                "CRITICAL",
                "Test CRITICAL 1",
            ],
            [
                "2025-12-16T00:01:00Z",
                "srx-fw01",
                "RT_IDP",
                "192.168.1.2 > 8.8.8.8",
                "192.168.1.2",
                "private",
                "8.8.8.8",
                "global",
                "tcp",
                "4",
                "WARNING",
                "Test WARNING 1",
            ],
        ]
        rows2 = [
            [
                "2025-12-16T01:00:00Z",
                "srx-fw01",
                "RT_IDP",
                "10.0.0.1 > 1.1.1.1",
                "10.0.0.1",
                "private",
                "1.1.1.1",
                "global",
                "udp",
                "2",
                "CRITICAL",
                "Test CRITICAL 2",
            ],
            [
                "2025-12-16T01:01:00Z",
                "srx-fw01",
                "RT_IDP",
                "10.0.0.2 > 1.1.1.1",
                "10.0.0.2",
                "private",
                "1.1.1.1",
                "global",
                "udp",
                "4",
                "WARNING",
                "Test WARNING 2",
            ],
        ]

        input_path1 = temp_dir / "test1.csv"
        input_path2 = temp_dir / "test2.csv"
        output_file = temp_dir / "critical_merged.csv"

        create_test_csv(input_path1, rows1)
        create_test_csv(input_path2, rows2)

        # 実行
        result = filter_and_merge_critical(
            [input_path1, input_path2], output_file, verbose=False
        )

        # 検証
        assert result is not None
        df = pd.read_csv(result, keep_default_na=False)

        # CRITICAL行のみ（2ファイルから各1行 = 計2行）
        assert len(df) == 2
        assert all(df["Severity"] == "CRITICAL")

        # 両方のファイルからのデータが含まれている
        assert "192.168.1.1" in df["srcIP"].values
        assert "10.0.0.1" in df["srcIP"].values

    def test_filter_critical_no_critical_rows(self, temp_dir):
        """正常系: CRITICAL行がない場合はNoneを返す"""
        rows = [
            [
                "2025-12-16T00:00:00Z",
                "srx-fw01",
                "RT_IDP",
                "192.168.1.5 > 8.8.8.8",
                "192.168.1.5",
                "private",
                "8.8.8.8",
                "global",
                "tcp",
                "4",
                "WARNING",
                "Test WARNING only",
            ],
        ]

        input_path = temp_dir / "test.csv"
        output_file = temp_dir / "critical_merged.csv"
        create_test_csv(input_path, rows)

        # 実行
        result = filter_and_merge_critical([input_path], output_file, verbose=False)

        # 検証: CRITICAL行がないのでNoneを返す
        assert result is None
        assert not output_file.exists()

    def test_filter_critical_missing_severity_column(self, temp_dir):
        """異常系: Severity列が存在しない場合はエラー"""
        # Severity列がないCSVを作成
        csv_path = temp_dir / "test.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Hostname"])
            writer.writerow(["2025-12-16T00:00:00Z", "srx-fw01"])

        output_file = temp_dir / "critical_merged.csv"

        # 実行 & 検証
        with pytest.raises(FilterCriticalError, match="Severity列が見つかりません"):
            filter_and_merge_critical([csv_path], output_file, verbose=False)
