@echo off
REM Juniper Syslog Filter - GUI起動スクリプト

echo ========================================
echo  Juniper Syslog Filter - GUI起動中...
echo ========================================
echo.

REM プロジェクトディレクトリに移動
cd /d "%~dp0"

REM 仮想環境を有効化
call venv\Scripts\activate.bat

REM Streamlit GUIを起動
echo [INFO] ブラウザが自動で開きます...
echo [INFO] 終了するにはこのウィンドウを閉じてください
echo.

streamlit run run_gui.py

REM 終了時の処理
echo.
echo ========================================
echo  処理が終了しました
echo ========================================
pause