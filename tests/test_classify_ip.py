"""
test_classify_ip.py - classify_ip.pyのテストコード

IP分類機能（pandas + ファイル出力版）をテスト
"""

import pytest
import pandas as pd
import csv
from pathlib import Path
from modules.classify_ip import (
    classify_ip,
    classify_ip_address,
    is_private_ip,
    ClassifyIPError,
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
            ["Timestamp", "Hostname", "AppName", "routing", "srcIP", "dstIP", "Message"]
        )
        writer.writerows(rows)


class TestIPClassification:
    """IP分類関数のテスト"""

    def test_is_private_ip(self):
        """正常系: プライベートIP判定"""
        # 10.x.x.x
        assert is_private_ip("10.0.0.1") == True
        assert is_private_ip("10.255.255.255") == True

        # 172.16-31.x.x
        assert is_private_ip("172.16.0.1") == True
        assert is_private_ip("172.31.255.255") == True
        assert is_private_ip("172.15.0.1") == False  # 範囲外
        assert is_private_ip("172.32.0.1") == False  # 範囲外

        # 192.168.x.x
        assert is_private_ip("192.168.0.1") == True
        assert is_private_ip("192.168.255.255") == True

        # グローバルIP
        assert is_private_ip("8.8.8.8") == False
        assert is_private_ip("203.0.113.10") == False

        # 無効なIP
        assert is_private_ip("") == False
        assert is_private_ip("invalid") == False

    def test_classify_ip_address(self):
        """正常系: IP分類"""
        assert classify_ip_address("192.168.1.1") == "private"
        assert classify_ip_address("10.0.0.1") == "private"
        assert classify_ip_address("8.8.8.8") == "global"
        assert classify_ip_address("") == ""


class TestClassifyIP:
    """classify_ip関数のテスト"""

    def test_classify_ip_basic(self, temp_dir):
        """正常系: IP分類が正しく動作する"""
        # テストデータ作成
        rows = [
            [
                "2025-12-16T00:00:00Z",
                "srx-fw01",
                "RT_IDP",
                "192.168.1.5 > 8.8.8.8",
                "192.168.1.5",
                "8.8.8.8",
                "RT_IDP_ATTACK_LOG: SQL injection",
            ],
            [
                "2025-12-16T00:01:00Z",
                "srx-fw01",
                "RT_IDP",
                "10.0.0.1 > 203.0.113.10",
                "10.0.0.1",
                "203.0.113.10",
                "RT_IDP_ATTACK_LOG: Port scan",
            ],
        ]

        input_path = temp_dir / "test.csv"
        output_dir = temp_dir / "output"
        create_test_csv(input_path, rows)

        # 実行
        result = classify_ip([input_path], output_dir, verbose=False)

        # 検証: ファイルが作成される
        assert len(result) == 1
        assert result[0].exists()

        # 出力ファイルの内容を検証
        df = pd.read_csv(result[0], keep_default_na=False)

        # 列が正しく追加されている
        assert "srcIP_type" in df.columns
        assert "dstIP_type" in df.columns

        # 分類結果が正しい
        assert df.iloc[0]["srcIP_type"] == "private"
        assert df.iloc[0]["dstIP_type"] == "global"
        assert df.iloc[1]["srcIP_type"] == "private"
        assert df.iloc[1]["dstIP_type"] == "global"

        # 列の順序を確認（重要！）
        cols = df.columns.tolist()
        assert cols == [
            "Timestamp",
            "Hostname",
            "AppName",
            "routing",
            "srcIP",
            "srcIP_type",
            "dstIP",
            "dstIP_type",
            "Message",
        ]

    def test_classify_ip_empty_ip(self, temp_dir):
        """正常系: IPが空の場合は空文字列"""
        rows = [
            [
                "2025-12-16T00:00:00Z",
                "srx-fw01",
                "RT_FLOW",
                "",
                "",
                "",
                "RT_FLOW_SESSION_CREATE: session created",
            ],
        ]

        input_path = temp_dir / "test.csv"
        output_dir = temp_dir / "output"
        create_test_csv(input_path, rows)

        # 実行
        result = classify_ip([input_path], output_dir, verbose=False)

        # 検証
        df = pd.read_csv(result[0], keep_default_na=False)

        # IPが空の場合は分類も空
        assert df.iloc[0]["srcIP_type"] == ""
        assert df.iloc[0]["dstIP_type"] == ""

    def test_classify_ip_multiple_files(self, temp_dir):
        """正常系: 複数ファイルの処理"""
        rows1 = [
            [
                "2025-12-16T00:00:00Z",
                "srx-fw01",
                "RT_IDP",
                "192.168.1.1 > 8.8.8.8",
                "192.168.1.1",
                "8.8.8.8",
                "Test message 1",
            ]
        ]
        rows2 = [
            [
                "2025-12-16T01:00:00Z",
                "srx-fw01",
                "RT_IDP",
                "10.0.0.1 > 1.1.1.1",
                "10.0.0.1",
                "1.1.1.1",
                "Test message 2",
            ]
        ]

        input_path1 = temp_dir / "test1.csv"
        input_path2 = temp_dir / "test2.csv"
        output_dir = temp_dir / "output"

        create_test_csv(input_path1, rows1)
        create_test_csv(input_path2, rows2)

        # 実行
        result = classify_ip([input_path1, input_path2], output_dir, verbose=False)

        # 検証: 2ファイルが処理される
        assert len(result) == 2

        df1 = pd.read_csv(result[0], keep_default_na=False)
        df2 = pd.read_csv(result[1], keep_default_na=False)

        assert df1.iloc[0]["srcIP_type"] == "private"
        assert df1.iloc[0]["dstIP_type"] == "global"
        assert df2.iloc[0]["srcIP_type"] == "private"
        assert df2.iloc[0]["dstIP_type"] == "global"

    def test_classify_ip_missing_srcip_column(self, temp_dir):
        """異常系: srcIP列が存在しない場合はエラー"""
        # srcIP列がないCSVを作成
        csv_path = temp_dir / "test.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Hostname", "AppName", "Message"])
            writer.writerow(["2025-12-16T00:00:00Z", "srx-fw01", "RT_IDP", "Test"])

        output_dir = temp_dir / "output"

        # 実行 & 検証
        with pytest.raises(ClassifyIPError, match="srcIP列が見つかりません"):
            classify_ip([csv_path], output_dir, verbose=False)
