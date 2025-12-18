"""
filter_keyword.py - キーワードフィルタモジュール（pandas版）

責務:
- temp_extracted/*.csv から RT_IDP_ATTACK を含む行を抽出
- filtered_logs/*.csv に出力
- 内部的にpandasで高速処理
"""

from pathlib import Path
from typing import List, Union
import pandas as pd


class FilterError(Exception):
    """フィルタリング処理のカスタム例外"""

    pass


def filter_keyword(
    input_files: List[Path],
    output_dir: Union[str, Path],
    keyword: str = "RT_IDP_ATTACK",
) -> int:
    """
    CSVファイルをキーワードでフィルタリング

    Message列に指定されたキーワードを含む行のみを抽出し、
    ファイルとして出力する。内部的にpandasで高速処理。

    Args:
        input_files: 入力CSVファイルのリスト
        output_dir: 出力先ディレクトリ
        keyword: フィルタキーワード（デフォルト: "RT_IDP_ATTACK"）

    Returns:
        int: フィルタ後の総行数

    Raises:
        FilterError: フィルタリング処理に失敗した場合

    Examples:
        >>> count = filter_keyword(csv_files, "filtered_logs")
        >>> count = filter_keyword(csv_files, "filtered_logs", keyword="RT_SCREEN")
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    total_rows = 0

    for input_path in input_files:
        try:
            # pandasでCSVを読み込み
            df = pd.read_csv(input_path, encoding="utf-8")

            # Message列の存在確認
            if "Message" not in df.columns:
                raise FilterError(f"Message列が見つかりません: {input_path}")

            # キーワードでフィルタリング（部分一致、大文字小文字区別）
            filtered_df = df[
                df["Message"].str.contains(
                    keyword,
                    case=True,  # 大文字小文字を区別
                    na=False,  # NaNはFalse扱い（除外）
                )
            ]

            # フィルタ後に行が存在する場合のみ出力
            if len(filtered_df) > 0:
                # 出力ファイル名を生成（入力と同じファイル名）
                output_path = output_dir / input_path.name

                # pandasでCSVとして出力
                filtered_df.to_csv(output_path, index=False, encoding="utf-8")

                total_rows += len(filtered_df)

        except pd.errors.EmptyDataError:
            # 空のCSVファイルはスキップ
            continue

        except pd.errors.ParserError as e:
            raise FilterError(
                f"CSVの解析に失敗しました: {input_path}, エラー: {str(e)}"
            )

        except Exception as e:
            raise FilterError(
                f"フィルタリング中にエラーが発生しました: {input_path}, エラー: {str(e)}"
            )

    return total_rows


def main():
    """
    スタンドアロン実行用のメイン関数
    """
    # デフォルトパス設定
    project_root = Path(__file__).parent.parent
    input_dir = project_root / "temp_extracted"
    output_dir = project_root / "filtered_logs"

    print("=" * 60)
    print("Juniper Syslog Filter - キーワードフィルタ (pandas版)")
    print("=" * 60)

    # 入力ファイルを取得
    input_files = sorted(input_dir.glob("*.csv"))

    if not input_files:
        print(f"\n⚠️  入力ファイルが見つかりません: {input_dir}")
        return 0

    print(f"📄 対象ファイル数: {len(input_files)}")
    print(f"🔍 キーワード: RT_IDP_ATTACK")

    try:
        total_rows = filter_keyword(input_files, output_dir, keyword="RT_IDP_ATTACK")

        print(f"\n✅ フィルタリング完了")
        print(f"📊 抽出された行数: {total_rows:,}")

    except FilterError as e:
        print(f"\n❌ エラーが発生しました: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
