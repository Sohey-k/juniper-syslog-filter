"""
test_extract_routing.py - extract_routing.pyモジュールのテストコード
"""

import pytest
import csv
from pathlib import Path
import tempfile

from modules.extract_routing import (
    extract_routing_from_message,
    extract_routing_from_csv,
    extract_routing,
    ExtractRoutingError,
)


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
        writer.writerow(["Timestamp", "Hostname", "AppName", "Message"])
        # routing抽出できる行
        writer.writerow(
            [
                "2025-12-16T00:11:01Z",
                "srx-fw01",
                "RT_IDP",
                "RT_IDP_ATTACK_LOG: Malware detected 192.168.195.70/14888 > 30.84.98.42/22 protocol=tcp",
            ]
        )
        # routing抽出できる行（別パターン）
        writer.writerow(
            [
                "2025-12-16T00:16:22Z",
                "srx-fw01",
                "RT_IDP",
                "RT_IDP_ATTACK_LOG: Port scan detected 10.0.0.5/12345 > 203.0.113.10/80 protocol=udp",
            ]
        )
        # routing抽出できない行
        writer.writerow(
            [
                "2025-12-16T00:20:00Z",
                "srx-fw01",
                "RT_FLOW",
                "RT_FLOW_SESSION_CLOSE: session closed",
            ]
        )


# ============================================================================
# extract_routing_from_message 関数のテスト
# ============================================================================


def test_extract_routing_from_message_success():
    """正常なrouting抽出のテスト"""
    message = (
        "RT_IDP_ATTACK_LOG: Attack 192.168.195.70/14888 > 30.84.98.42/22 protocol=tcp"
    )

    routing = extract_routing_from_message(message)

    assert routing == "192.168.195.70 > 30.84.98.42"


def test_extract_routing_from_message_no_match():
    """routing情報がない場合のテスト"""
    message = "RT_FLOW_SESSION_CLOSE: session closed"

    routing = extract_routing_from_message(message)

    assert routing is None


def test_extract_routing_from_message_various_ips():
    """様々なIPアドレスパターンのテスト"""
    test_cases = [
        ("Attack 10.0.0.5/12345 > 203.0.113.10/80", "10.0.0.5 > 203.0.113.10"),
        ("Scan 172.16.0.1/54321 > 8.8.8.8/443", "172.16.0.1 > 8.8.8.8"),
        (
            "Traffic 192.168.1.100/8080 > 192.168.1.200/9090",
            "192.168.1.100 > 192.168.1.200",
        ),
    ]

    for message, expected in test_cases:
        routing = extract_routing_from_message(message)
        assert routing == expected


# ============================================================================
# extract_routing_from_csv 関数のテスト
# ============================================================================


def test_extract_routing_from_csv_success(temp_dirs):
    """CSVファイルからのrouting抽出テスト"""
    input_dir, output_dir = temp_dirs
    input_path = input_dir / "test.csv"
    output_path = output_dir / "routed.csv"

    # テストCSVを作成
    create_test_csv(input_path)

    # routing抽出実行
    row_count = extract_routing_from_csv(input_path, output_path, verbose=False)

    # 検証: 4行処理（ヘッダー + 3行）
    assert row_count == 4
    assert output_path.exists()

    # 出力ファイルの内容を確認
    with open(output_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

        # ヘッダー確認（5列: Timestamp, Hostname, AppName, routing, Message）
        assert len(rows[0]) == 5
        assert rows[0] == ["Timestamp", "Hostname", "AppName", "routing", "Message"]

        # 1行目: routing抽出成功
        assert rows[1][3] == "192.168.195.70 > 30.84.98.42"

        # 2行目: routing抽出成功
        assert rows[2][3] == "10.0.0.5 > 203.0.113.10"

        # 3行目: routing抽出失敗（空文字）
        assert rows[3][3] == ""


def test_extract_routing_from_csv_file_not_found(temp_dirs):
    """存在しないファイルのテスト"""
    input_dir, output_dir = temp_dirs
    input_path = input_dir / "nonexistent.csv"
    output_path = output_dir / "routed.csv"

    with pytest.raises(FileNotFoundError):
        extract_routing_from_csv(input_path, output_path, verbose=False)


# ============================================================================
# extract_routing 関数のテスト
# ============================================================================


def test_extract_routing_multiple_files(temp_dirs):
    """複数ファイルのrouting抽出テスト"""
    input_dir, output_dir = temp_dirs

    # 2つのテストCSVを作成
    input_files = []
    for i in range(2):
        csv_path = input_dir / f"test_{i:02d}.csv"
        create_test_csv(csv_path)
        input_files.append(csv_path)

    # routing抽出実行
    output_files = extract_routing(input_files, output_dir, verbose=False)

    # 検証: 2ファイル作成
    assert len(output_files) == 2

    # 各ファイルが5列になっているか確認
    for output_file in output_files:
        with open(output_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            assert len(header) == 5
            assert header[3] == "routing"


def test_extract_routing_empty_list(temp_dirs):
    """入力ファイルが空の場合のテスト"""
    input_dir, output_dir = temp_dirs

    output_files = extract_routing([], output_dir, verbose=False)

    # 検証: 空のリストが返る
    assert output_files == []


# ============================================================================
# 実行
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
