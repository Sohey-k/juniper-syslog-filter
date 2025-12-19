"""
cleanup_all.py - 全ディレクトリクリーンアップモジュール

責務:
- パイプライン実行後の中間ディレクトリを全削除
- source_logs/ と final_output/ は保持
- ストレージの圧迫を防止

削除対象:
    temp_extracted/
    filtered_logs/
    merged_logs/
    reduced_logs/
    routed_logs/
    splitted_logs/
    classified_logs/
    protocol_extracted/
    severity_level_extracted/
    severity_extracted/
    critical_only/
"""

from pathlib import Path
from typing import Union
import shutil


class CleanupAllError(Exception):
    """クリーンアップ処理のカスタム例外"""

    pass


def cleanup_all_directories(
    project_root: Union[str, Path], verbose: bool = True
) -> int:
    """
    パイプライン実行後の中間ディレクトリを全削除

    source_logs/ と final_output/ 以外の全ディレクトリを削除する。
    ディレクトリが存在しない場合はスキップ。

    Args:
        project_root: プロジェクトルートディレクトリ
        verbose: 詳細ログを出力するか

    Returns:
        int: 削除されたディレクトリ数

    Raises:
        CleanupAllError: クリーンアップ処理に失敗した場合

    Examples:
        >>> count = cleanup_all_directories(Path("."), verbose=True)
        >>> print(f"{count}個のディレクトリを削除しました")
    """
    project_root = Path(project_root)

    # 削除対象ディレクトリのリスト
    target_dirs = [
        "temp_extracted",
        "filtered_logs",
        "merged_logs",
        "reduced_logs",
        "routed_logs",
        "splitted_logs",
        "classified_logs",
        "protocol_extracted",
        "severity_level_extracted",
        "severity_extracted",
        "critical_only",
    ]

    deleted_count = 0

    try:
        for dir_name in target_dirs:
            dir_path = project_root / dir_name

            if dir_path.exists() and dir_path.is_dir():
                # ディレクトリ内のファイル数をカウント（オプション）
                if verbose:
                    file_count = len(list(dir_path.glob("*")))
                    print(
                        f"  🗑️  {dir_name}/ を削除中... ({file_count}ファイル)",
                        end=" ",
                    )

                # ディレクトリごと削除
                shutil.rmtree(dir_path)
                deleted_count += 1

                if verbose:
                    print("✓")

        if verbose:
            if deleted_count > 0:
                print(f"\n✅ クリーンアップ完了: {deleted_count}個のディレクトリを削除")
            else:
                print("\n⚠️  削除対象のディレクトリがありませんでした")

        return deleted_count

    except PermissionError as e:
        raise CleanupAllError(f"ディレクトリの削除権限がありません: {e}")

    except Exception as e:
        raise CleanupAllError(f"クリーンアップ処理中にエラーが発生しました: {e}")


def main():
    """
    スタンドアロン実行用のメイン関数
    """
    # プロジェクトルートを取得
    project_root = Path(__file__).parent.parent

    print("=" * 70)
    print("Juniper Syslog Filter - 全ディレクトリクリーンアップ")
    print("=" * 70)
    print()
    print("⚠️  以下のディレクトリを削除します:")
    print("   - temp_extracted/")
    print("   - filtered_logs/")
    print("   - merged_logs/")
    print("   - reduced_logs/")
    print("   - routed_logs/")
    print("   - splitted_logs/")
    print("   - classified_logs/")
    print("   - protocol_extracted/")
    print("   - severity_level_extracted/")
    print("   - severity_extracted/")
    print("   - critical_only/")
    print()
    print("✅ 保持されるディレクトリ:")
    print("   - source_logs/")
    print("   - final_output/")
    print()

    # 確認プロンプト
    response = input("実行しますか？ (yes/no): ").strip().lower()

    if response not in ["yes", "y"]:
        print("\n❌ クリーンアップをキャンセルしました")
        return 0

    print()
    print("-" * 70)

    try:
        deleted_count = cleanup_all_directories(project_root, verbose=True)

        print("-" * 70)
        if deleted_count > 0:
            print(f"\n✅ 処理完了: {deleted_count}個のディレクトリを削除しました")
        else:
            print("\n⚠️  削除対象のディレクトリがありませんでした")

    except CleanupAllError as e:
        print(f"\n❌ エラーが発生しました: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
