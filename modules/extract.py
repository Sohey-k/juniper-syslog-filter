"""
extract.py - ZIP展開モジュール

責務:
- source_logs/*.zip を temp_extracted/*.csv に展開
- エラーハンドリング
- ログ出力
"""

import zipfile
import os
import shutil
from pathlib import Path
from typing import List


class ExtractError(Exception):
    """ZIP展開時のカスタム例外"""
    pass


def extract_zip(zip_path: Path, output_dir: Path) -> List[Path]:
    """
    ZIPファイルを展開し、CSVファイルのパスリストを返す
    
    Args:
        zip_path: 展開するZIPファイルのパス
        output_dir: 展開先ディレクトリ
        
    Returns:
        展開されたCSVファイルのPathリスト
        
    Raises:
        ExtractError: ZIP展開に失敗した場合
        FileNotFoundError: ZIPファイルが存在しない場合
    """
    if not zip_path.exists():
        raise FileNotFoundError(f"ZIPファイルが見つかりません: {zip_path}")
    
    if not zip_path.suffix == '.zip':
        raise ExtractError(f"ZIPファイルではありません: {zip_path}")
    
    # 出力ディレクトリが存在しない場合は作成
    output_dir.mkdir(parents=True, exist_ok=True)
    
    extracted_files = []
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # ZIPファイルの内容をリスト化
            file_list = zip_ref.namelist()
            
            if not file_list:
                raise ExtractError(f"ZIPファイルが空です: {zip_path}")
            
            # 全ファイルを展開
            zip_ref.extractall(output_dir)
            
            # 展開されたCSVファイルのパスを収集
            for filename in file_list:
                file_path = output_dir / filename
                if file_path.suffix == '.csv' and file_path.exists():
                    extracted_files.append(file_path)
            
            if not extracted_files:
                raise ExtractError(f"CSVファイルが見つかりませんでした: {zip_path}")
                
    except zipfile.BadZipFile:
        raise ExtractError(f"破損したZIPファイルです: {zip_path}")
    except Exception as e:
        raise ExtractError(f"ZIP展開中にエラーが発生しました: {zip_path}, エラー: {str(e)}")
    
    return extracted_files


def extract_all_zips(source_dir: Path, output_dir: Path, verbose: bool = True) -> List[Path]:
    """
    指定ディレクトリ内の全ZIPファイルを展開
    
    Args:
        source_dir: ZIPファイルが格納されているディレクトリ
        output_dir: 展開先ディレクトリ
        verbose: 詳細ログを出力するか
        
    Returns:
        展開された全CSVファイルのPathリスト
        
    Raises:
        FileNotFoundError: source_dirが存在しない場合
    """
    if not source_dir.exists():
        raise FileNotFoundError(f"ソースディレクトリが見つかりません: {source_dir}")
    
    # ZIPファイルのリストを取得
    zip_files = sorted(source_dir.glob("*.zip"))
    
    if not zip_files:
        if verbose:
            print(f"⚠️  ZIPファイルが見つかりませんでした: {source_dir}")
        return []
    
    all_extracted_files = []
    success_count = 0
    error_count = 0
    
    for zip_path in zip_files:
        try:
            if verbose:
                print(f"📦 展開中: {zip_path.name}...", end=" ")
            
            extracted_files = extract_zip(zip_path, output_dir)
            all_extracted_files.extend(extracted_files)
            success_count += 1
            
            if verbose:
                print(f"✓ ({len(extracted_files)}ファイル)")
                
        except (ExtractError, FileNotFoundError) as e:
            error_count += 1
            if verbose:
                print(f"✗ エラー: {str(e)}")
    
    if verbose:
        print(f"\n✅ 展開完了: {success_count}個成功, {error_count}個失敗")
        print(f"📄 抽出されたCSVファイル数: {len(all_extracted_files)}")
    
    return all_extracted_files


def main():
    """
    スタンドアロン実行用のメイン関数
    """
    # デフォルトパス設定
    project_root = Path(__file__).parent.parent
    source_dir = project_root / "source_logs"
    output_dir = project_root / "temp_extracted"
    
    print("=" * 60)
    print("Juniper Syslog Filter - ZIP展開モジュール")
    print("=" * 60)
    
    try:
        extracted_files = extract_all_zips(source_dir, output_dir, verbose=True)
        
        if extracted_files:
            print(f"\n✅ 処理完了: {len(extracted_files)}個のCSVファイルを展開しました")
        else:
            print("\n⚠️  展開されたファイルがありません")
            
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())