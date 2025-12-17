"""
test_split_ip.py - split_ip.pyモジュールのテストコード
"""

import pytest
import csv
from pathlib import Path
import tempfile

from modules.split_ip import split_routing, split_ip_from_csv, split_ip, SplitIPError


@pytest.fixture
def temp_dirs():
    """テスト用の一時ディレクトリを作成"""
    with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as output_dir:
        yield Path(input_dir), Path(output_dir)


def create_test_csv(path: Path):
    """テスト用のCSVファイルを作成"""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # ヘッダー
        writer.writerow(["Timestamp", "Hostname", "AppName", "routing", "Message"])
        # routing分割できる行
        writer.writerow(
            [
                "2025-12-16T00:11:01Z",
                "srx-fw01",
                "RT_IDP",
                "192.168.195.70 > 30.84.98.42",
                "RT_IDP_ATTACK_LOG: Malware detected",
            ]
        )
        # routing分割できる行（別パターン）
        writer.writerow(
            [
                "2025-12-16T00:16:22Z",
                "srx-fw01",
                "RT_IDP",
                "10.0.0.5 > 203.0.113.10",
                "RT_IDP_ATTACK_LOG: Port scan detected",
            ]
        )
        # routing が空の行
        writer.writerow(
            [
                "2025-12-16T00:20:00Z",
                "srx-fw01",
                "RT_FLOW",
                "",
                "RT_FLOW_SESSION_CLOSE: session closed",
            ]
        )


# ============================================================================
# split_routing 関数のテスト
# ============================================================================


def test_split_routing_success():
    """正常なrouting分割のテスト"""
    routing = "192.168.195.70 > 30.84.98.42"

    src_ip, dst_ip = split_routing(routing)

    assert src_ip == "192.168.195.70"
    assert dst_ip == "30.84.98.42"


def test_split_routing_empty():
    """空のrouting文字列のテスト"""
    routing = ""

    src_ip, dst_ip = split_routing(routing)

    assert src_ip == ""
    assert dst_ip == ""


def test_split_routing_various_patterns():
    """様々なIPアドレスパターンのテスト"""
    test_cases = [
        ("10.0.0.5 > 203.0.113.10", ("10.0.0.5", "203.0.113.10")),
        ("172.16.0.1 > 8.8.8.8", ("172.16.0.1", "8.8.8.8")),
        ("192.168.1.100 > 192.168.1.200", ("192.168.1.100", "192.168.1.200")),
    ]

    for routing, (expected_src, expected_dst) in test_cases:
        src_ip, dst_ip = split_routing(routing)
        assert src_ip == expected_src
        assert dst_ip == expected_dst


# ============================================================================
# split_ip_from_csv 関数のテスト
# ============================================================================


def test_split_ip_from_csv_success(temp_dirs):
    """CSVファイルからのIP分割テスト"""
    input_dir, output_dir = temp_dirs
    input_path = input_dir / "test.csv"
    output_path = output_dir / "splitted.csv"

    # テストCSVを作成
    create_test_csv(input_path)

    # IP分割実行
    row_count = split_ip_from_csv(input_path, output_path, verbose=False)

    # 検証: 4行処理（ヘッダー + 3行）
    assert row_count == 4
    assert output_path.exists()

    # 出力ファイルの内容を確認
    with open(output_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

        # ヘッダー確認（7列: Timestamp, Hostname, AppName, routing, srcIP, dstIP, Message）
        assert len(rows[0]) == 7
        assert rows[0] == [
            "Timestamp",
            "Hostname",
            "AppName",
            "routing",
            "srcIP",
            "dstIP",
            "Message",
        ]

        # 1行目: IP分割成功
        assert rows[1][4] == "192.168.195.70"  # srcIP
        assert rows[1][5] == "30.84.98.42"  # dstIP

        # 2行目: IP分割成功
        assert rows[2][4] == "10.0.0.5"  # srcIP
        assert rows[2][5] == "203.0.113.10"  # dstIP

        # 3行目: routing空（空文字）
        assert rows[3][4] == ""  # srcIP
        assert rows[3][5] == ""  # dstIP


def test_split_ip_from_csv_file_not_found(temp_dirs):
    """存在しないファイルのテスト"""
    input_dir, output_dir = temp_dirs
    input_path = input_dir / "nonexistent.csv"
    output_path = output_dir / "splitted.csv"

    with pytest.raises(FileNotFoundError):
        split_ip_from_csv(input_path, output_path, verbose=False)


# ============================================================================
# split_ip 関数のテスト
# ============================================================================


def test_split_ip_multiple_files(temp_dirs):
    """複数ファイルのIP分割テスト"""
    input_dir, output_dir = temp_dirs

    # 2つのテストCSVを作成
    input_files = []
    for i in range(2):
        csv_path = input_dir / f"test_{i:02d}.csv"
        create_test_csv(csv_path)
        input_files.append(csv_path)

    # IP分割実行
    output_files = split_ip(input_files, output_dir, verbose=False)

    # 検証: 2ファイル作成
    assert len(output_files) == 2

    # 各ファイルが7列になっているか確認
    for output_file in output_files:
        with open(output_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            assert len(header) == 7
            assert header[4] == "srcIP"
            assert header[5] == "dstIP"


def test_split_ip_empty_list(temp_dirs):
    """入力ファイルが空の場合のテスト"""
    input_dir, output_dir = temp_dirs

    output_files = split_ip([], output_dir, verbose=False)

    # 検証: 空のリストが返る
    assert output_files == []


# ============================================================================
# 実行
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
