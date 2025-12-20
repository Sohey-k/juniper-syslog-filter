"""
Excel出力モジュール（xlsxwriter版 - 高速）

critical_only/*.csv を Excel形式で出力
- フォント: 游ゴシック 11pt
- ヘッダー: 太字
- 列幅: 自動調整
- openpyxlより2-3倍速い
"""

from pathlib import Path
from typing import Union
import pandas as pd


class ExportExcelError(Exception):
    """Excel出力処理でのエラー"""

    pass


def export_to_excel(
    input_file: Union[str, Path],
    output_dir: Union[str, Path],
    font_name: str = "游ゴシック",
    font_size: int = 11,
    min_width: int = 10,
    max_width: int = 50,
    verbose: bool = True,
) -> Path:
    """
    CSVファイルをExcel形式で出力（xlsxwriter使用 - 高速）

    Args:
        input_file: 入力CSVファイルのパス
        output_dir: 出力先ディレクトリ
        font_name: フォント名
        font_size: フォントサイズ
        min_width: 列の最小幅
        max_width: 列の最大幅
        verbose: 詳細ログを出力するか

    Returns:
        Path: 出力されたExcelファイルのPath

    Raises:
        ExportExcelError: Excel出力に失敗した場合

    Examples:
        >>> from pathlib import Path
        >>> output = export_to_excel(
        ...     Path("critical_only/critical_001.csv"),
        ...     Path("final_output"),
        ...     verbose=True
        ... )
        >>> print(output)
        final_output/critical_001.xlsx
    """
    input_path = Path(input_file)
    output_dir = Path(output_dir)

    # 入力ファイルの存在確認
    if not input_path.exists():
        raise ExportExcelError(f"入力ファイルが存在しません: {input_path}")

    # 出力ディレクトリの作成
    output_dir.mkdir(parents=True, exist_ok=True)

    # 出力ファイルパス（.csv → .xlsx）
    output_filename = input_path.stem + ".xlsx"
    output_path = output_dir / output_filename

    try:
        # pandasでCSVを読み込み
        df = pd.read_csv(input_path, encoding="utf-8", keep_default_na=False)

        if verbose:
            print(f"  📄 入力: {input_path.name} ({len(df)}行)")

        # xlsxwriterでExcel出力（高速）
        writer = pd.ExcelWriter(output_path, engine="xlsxwriter")
        df.to_excel(writer, index=False, sheet_name="Sheet1")

        # ワークブックとワークシートを取得
        workbook = writer.book
        worksheet = writer.sheets["Sheet1"]

        # フォーマット定義
        header_format = workbook.add_format(
            {"font_name": font_name, "font_size": font_size, "bold": True}
        )

        cell_format = workbook.add_format(
            {"font_name": font_name, "font_size": font_size}
        )

        # ヘッダー行にフォーマット適用
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)

        # 列幅自動調整
        for i, col in enumerate(df.columns):
            # 列の最大文字数を計算
            # ヘッダーとデータの両方から最大長を取得
            column_len = df[col].astype(str).str.len().max()
            column_len = (
                max(column_len, len(str(col)))
                if not pd.isna(column_len)
                else len(str(col))
            )

            # 日本語補正（127以上のコードポイントがあれば）
            if df[col].astype(str).str.contains("[^\x00-\x7f]", regex=True).any():
                column_len = int(column_len * 1.5)

            # 幅設定（最小・最大制限）
            adjusted_width = min(max(column_len + 2, min_width), max_width)
            worksheet.set_column(i, i, adjusted_width, cell_format)

        # 保存
        writer.close()

        if verbose:
            print(f"  ✨ フォーマット適用完了")
            print(f"  💾 出力: {output_path}")

        return output_path

    except Exception as e:
        raise ExportExcelError(f"Excel出力に失敗しました: {e}")
