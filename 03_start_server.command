@echo off
:: 文字コードをUTF-8に変更して文字化けを防ぐ
chcp 65001 >nul

:: カレントディレクトリをこのバッチファイルの場所に移動
cd /d %~dp0

echo ========================================================
echo  Local Server Started
echo  Please do not close this window.
echo ========================================================

:: サーバー起動より少し先にブラウザを開く
start "" "http://localhost:8000/output/"

:: Pythonでサーバーを起動 (ポート8000)
python -m http.server 8000

:: エラーハンドリング
if %errorlevel% neq 0 (
    echo.
    echo [Error] Python not found.
    pause
)