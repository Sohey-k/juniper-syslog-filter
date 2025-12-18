"""
test_split_ip.py - split_ip.pyのテストコード

IP分割機能（pandas + ファイル出力版）をテスト
"""

import pytest
import pandas as pd
import csv
from pathlib import Path
from modules.split_ip import split_ip, SplitIPError


@pytest.fixture
def temp_dir(tmp_path):
    """一時ディレクトリのフィクスチャ"""
    return tmp_path


def create_test_csv(csv_path: Path, rows: list):
    """テスト用CSVファイルを作成"""
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp", "Hostname", "AppName", "routing", "Message"])
        writer.writerows(rows)


class TestSplitIP:
    """split_ip関数のテスト"""

    def test_split_ip_basic(self, temp_dir):
        """正常系: routing列が正しく分割される"""
        # テストデータ作成
        rows = [
            [
                "2025-12-16T00:00:00Z",
                "srx-fw01",
                "RT_IDP",
                "192.168.1.5 > 203.0.113.10",
                "RT_IDP_ATTACK_LOG: SQL injection",
            ],
            [
                "2025-12-16T00:01:00Z",
                "srx-fw01",
                "RT_IDP",
                "10.0.0.100 > 8.8.8.8",
                "RT_IDP_ATTACK_LOG: Port scan",
            ],
        ]

        input_path = temp_dir / "test.csv"
        output_dir = temp_dir / "output"
        create_test_csv(input_path, rows)

        # 実行
        result = split_ip([input_path], output_dir, verbose=False)

        # 検証: ファイルが作成される
        assert len(result) == 1
        assert result[0].exists()

        # 出力ファイルの内容を検証
        df = pd.read_csv(result[0], keep_default_na=False)

        # 列が正しく追加されている
        assert "srcIP" in df.columns
        assert "dstIP" in df.columns

        # 分割結果が正しい
        assert df.iloc[0]["srcIP"] == "192.168.1.5"
        assert df.iloc[0]["dstIP"] == "203.0.113.10"
        assert df.iloc[1]["srcIP"] == "10.0.0.100"
        assert df.iloc[1]["dstIP"] == "8.8.8.8"

        # 列の順序を確認
        cols = df.columns.tolist()
        assert cols == [
            "Timestamp",
            "Hostname",
            "AppName",
            "routing",
            "srcIP",
            "dstIP",
            "Message",
        ]

    def test_split_ip_empty_routing(self, temp_dir):
        """正常系: routing列が空の場合は空文字列"""
        rows = [
            [
                "2025-12-16T00:00:00Z",
                "srx-fw01",
                "RT_FLOW",
                "",
                "RT_FLOW_SESSION_CREATE: session created",
            ],
            [
                "2025-12-16T00:01:00Z",
                "srx-fw01",
                "RT_IDP",
                "192.168.1.5 > 203.0.113.10",
                "RT_IDP_ATTACK_LOG: SQL injection",
            ],
        ]

        input_path = temp_dir / "test.csv"
        output_dir = temp_dir / "output"
        create_test_csv(input_path, rows)

        # 実行
        result = split_ip([input_path], output_dir, verbose=False)

        # 検証
        df = pd.read_csv(result[0], keep_default_na=False)

        # routing列が空の行は srcIP, dstIP も空
        assert df.iloc[0]["srcIP"] == ""
        assert df.iloc[0]["dstIP"] == ""

        # routing列がある行は正しく分割
        assert df.iloc[1]["srcIP"] == "192.168.1.5"
        assert df.iloc[1]["dstIP"] == "203.0.113.10"

    def test_split_ip_multiple_files(self, temp_dir):
        """正常系: 複数ファイルの処理"""
        rows1 = [
            [
                "2025-12-16T00:00:00Z",
                "srx-fw01",
                "RT_IDP",
                "192.168.1.1 > 8.8.8.8",
                "Test message 1",
            ]
        ]
        rows2 = [
            [
                "2025-12-16T01:00:00Z",
                "srx-fw01",
                "RT_IDP",
                "10.0.0.1 > 1.1.1.1",
                "Test message 2",
            ]
        ]

        input_path1 = temp_dir / "test1.csv"
        input_path2 = temp_dir / "test2.csv"
        output_dir = temp_dir / "output"

        create_test_csv(input_path1, rows1)
        create_test_csv(input_path2, rows2)

        # 実行
        result = split_ip([input_path1, input_path2], output_dir, verbose=False)

        # 検証: 2ファイルが処理される
        assert len(result) == 2

        df1 = pd.read_csv(result[0], keep_default_na=False)
        df2 = pd.read_csv(result[1], keep_default_na=False)

        assert df1.iloc[0]["srcIP"] == "192.168.1.1"
        assert df1.iloc[0]["dstIP"] == "8.8.8.8"
        assert df2.iloc[0]["srcIP"] == "10.0.0.1"
        assert df2.iloc[0]["dstIP"] == "1.1.1.1"

    def test_split_ip_missing_routing_column(self, temp_dir):
        """異常系: routing列が存在しない場合はエラー"""
        # routing列がないCSVを作成
        csv_path = temp_dir / "test.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Hostname", "AppName", "Message"])
            writer.writerow(["2025-12-16T00:00:00Z", "srx-fw01", "RT_IDP", "Test"])

        output_dir = temp_dir / "output"

        # 実行 & 検証
        with pytest.raises(SplitIPError, match="routing列が見つかりません"):
            split_ip([csv_path], output_dir, verbose=False)
