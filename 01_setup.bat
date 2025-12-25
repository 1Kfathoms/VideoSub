:: ファイル名: 01_setup.bat
:: 仕様: PyTorch(GPU版)を明示的にインストールした後、その他の依存関係を入れる
:: 役割: 環境リセットと再構築（GPU対応版）

@echo off
chcp 65001 > nul

set ENV_NAME=video_learning_env

echo ========================================================
echo 環境修復セットアップを開始します (GPU対応版)
echo ========================================================

call conda deactivate
echo 既存の環境 '%ENV_NAME%' を削除しています...
call conda remove -n %ENV_NAME% --all -y

echo.
echo 新しいConda環境 '%ENV_NAME%' を作成しています...
call conda create -n %ENV_NAME% python=3.10 -y

echo.
echo 環境をアクティベートしています...
call conda activate %ENV_NAME%

echo.
echo 1. GPU版 PyTorch (CUDA 12.1) をインストールしています...
:: ここで明示的に --index-url を指定してインストール
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

echo.
echo 2. その他のライブラリをインストールしています...
pip install -r requirements.txt

echo.
echo ========================================================
echo 環境構築が完了しました。
echo ========================================================
pause