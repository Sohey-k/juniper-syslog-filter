# Juniper Syslog Filter

Juniper SRX syslogから脅威データを高速抽出・Excel出力するETLツール

## ✨ 特徴

- ⚡ **超高速処理**: 3,360万行を3分で処理（従来比40倍高速）
- 📊 **Excel自動出力**: フィルタ結果を自動でExcel化（xlsxwriter採用）
- 🖥️ **GUI/CLI両対応**: 使いやすいStreamlit GUIとCLI版
- ✅ **テスト完備**: 59テストで品質保証

## 🎯 背景

元職場で使われていたGUI自動化ツール（処理時間2時間、頻繁にフリーズ）を、Pythonで完全リライト。  
**処理時間を2時間から3分に短縮**し、安定した運用を実現しました。

### 改善結果

| 項目     | 旧ツール         | **本ツール**               |
| -------- | ---------------- | -------------------------- |
| 処理時間 | 2時間            | **3分** ⚡                  |
| 安定性   | 頻繁にクラッシュ | **エラーハンドリング完備** |
| 操作性   | マウス操作不可   | **バックグラウンド実行**   |

## 🚀 クイックスタート

### インストール

```powershell
# リポジトリのクローン
git clone https://github.com/Sohey-k/juniper-syslog-generator.git
cd juniper-syslog-generator

# 仮想環境の作成
uv venv
venv\Scripts\activate

# 依存パッケージのインストール
uv pip install -r requirements.txt
```

### テストデータの生成

```powershell
# 実務データ再現（3,360万行、脅威出現率0.5%）
python generator.py -o source_logs -r 1400000 -t 0.005

# 軽量テストデータ（480万行、脅威出現率50%）
python generator.py -o source_logs -r 200000 -t 0.5
```

## 📖 使い方

### CLI版（推奨：最速）

```powershell
python run.py
```

**実行結果**:
```
======================================================================
✅ Phase 1 完了 ⏱️  経過時間: 0分34秒
======================================================================
...
🎉 全処理完了！ ⏱️  合計実行時間: 3分1秒
======================================================================
```

**出力**:
```
final_output/
├── merged_001.xlsx
└── merged_002.xlsx
```

### Web GUI版（リアルタイム進捗表示）

```powershell
streamlit run run_gui.py
```

**機能**:
- リアルタイム進捗表示（Phase別）
- 経過時間表示
- パラメータ変更（キーワード・Severity）
- 出力ファイル一覧

### パラメータ変更（引数版）

```powershell
# キーワード・Severityを変更
python run_with_args.py --keyword RT_SCREEN --severity WARNING
```

## 🏗️ システム構成

### 処理フロー（12フェーズ）

```
ZIP展開 → キーワードフィルタ → マージ → 列削除 → routing抽出 
→ IP分離 → IP判定 → protocol抽出 → SeverityLevel抽出 
→ Severity抽出 → CRITICAL抽出 → Excel出力
```

### 技術スタック

- **Python 3.8+**
- **pandas**: 高速データ処理（ベクトル演算）
- **xlsxwriter**: Excel出力（openpyxlの2-3倍高速）
- **Streamlit**: Web UI
- **pytest**: テスト（59テストケース）

## 📊 パフォーマンス

| データ量     | 入力行数  | フィルタ後 | 処理時間（CLI） |
| ------------ | --------- | ---------- | --------------- |
| 実務データ   | 3,360万行 | 約2-20万行 | **3分1秒** ⚡    |
| テストデータ | 480万行   | 約120万行  | 6分32秒         |

**重要**: 処理時間はフィルタ後のデータ量に依存します。

## 🧪 テスト

```powershell
# 全テスト実行（59テスト）
pytest

# カバレッジ付き
pytest --cov=modules --cov-report=html
```

## 📚 ドキュメント

- **[設計書](DESIGN_DOCUMENT.md)** - 詳細な技術仕様・実装ガイド
  - システムアーキテクチャ
  - モジュール仕様
  - 開発環境セットアップ
  - pandas実装詳細

## 🔧 開発環境

### 必要要件

- Python 3.8以上
- メモリ 16GB以上（32GB推奨）
- Windows環境

### 推奨ツール

- VSCode
- uv（パッケージ管理）
- Git

## 📝 ライセンス

MIT License

## 👤 作者

**Sohey-k**

- GitHub: [@Sohey-k](https://github.com/Sohey-k)
- 実務経験を基にした、実践的なETLツール開発

## 🙏 謝辞

本プロジェクトの開発において、生成AI（ChatGPT/Claude）を設計整理・コード品質向上のサポートツールとして活用しました。