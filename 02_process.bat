:: 仕様: ドラッグ＆ドロップされた動画ファイルをPythonスクリプトに渡す
:: 役割: Conda環境を有効化し、処理を実行するランチャー

@echo off

:: 文字コードをUTF-8 (CP65001) に変更し、その出力メッセージを非表示にする
chcp 65001 > nul

set ENV_NAME=video_learning_env

if "%~1"=="" (
    echo 動画ファイルをこのバッチファイルにドラッグ＆ドロップしてください。
    pause
    exit /b
)

echo 環境をアクティベートしています...
call conda activate %ENV_NAME%

echo 処理を開始します...
python process_video.py "%~1"

echo.
echo 処理が完了しました。何かキーを押すと終了します。
pause