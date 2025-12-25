# 仕様:
# 1. 動画ファイルを入力として受け取る
# 2. stable-ts (Whisper) で単語レベルのタイムスタンプ付き文字起こしを実行 (GPU使用)
# 3. argostranslate でセグメントごとに翻訳
# 4. outputフォルダを作成（フォルダ名は元のファイル名を維持）
# 5. 動画ファイルを「Web安全なファイル名（半角英数）」にリネームして出力フォルダへ移動し、data.js と index.html を生成する
#
# 使い方: python process_video.py "動画ファイルのパス"

import os
import sys
import json
import shutil
import re
import stable_whisper
import argostranslate.package
import argostranslate.translate
import torch

def setup_argostranslate():
    """翻訳モデルのダウンロードとセットアップ"""
    print("翻訳モデルを確認中...")
    argostranslate.package.update_package_index()
    available_packages = argostranslate.package.get_available_packages()
    # 英日翻訳パッケージを探す
    package_to_install = next(
        filter(
            lambda x: x.from_code == "en" and x.to_code == "ja", available_packages
        ), None
    )
    if package_to_install:
        # 既にインストール済みかチェックするロジックはライブラリ側にあるが、念のためdownload実行
        argostranslate.package.install_from_path(package_to_install.download())
        print("翻訳モデルをロードしました。")
    else:
        print("翻訳モデルが見つかりませんでした。")

def get_safe_filename(filename):
    """
    ファイル名からブラウザで問題になりやすい文字（日本語、スペース、特殊記号）を除去する。
    半角英数字、ドット(.)、ハイフン(-)、アンダースコア(_) 以外はすべてアンダースコアに置換。
    """
    safe_name = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    return safe_name

def process_video(video_path):
    # パス設定
    filename = os.path.basename(video_path)
    name_without_ext = os.path.splitext(filename)[0]
    
    # フォルダ名は元のファイル名（日本語可）を使用
    output_dir = os.path.join("output", name_without_ext)
    
    # 動画ファイル名はWeb安全な名前に変換
    safe_filename = get_safe_filename(filename)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"処理開始: {filename}")
    print(f"出力フォルダ: {output_dir}")
    print(f"保存ファイル名: {safe_filename}")

    # 1. GPUチェックとWhisperモデルロード
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")
    
    # モデルロード
    model = stable_whisper.load_model("large-v3", device=device)

    # 2. 文字起こし実行 (stable-ts)
    # 注意: 移動前のファイルパスを使用します
    print("文字起こしを実行中...")
    result = model.transcribe(video_path, language="en", regroup=True)

    # 3. 翻訳とデータ構造の整形
    print("翻訳を実行中...")
    setup_argostranslate()
    
    final_data = []
    
    for segment in result.segments:
        original_text = segment.text.strip()
        
        # 翻訳実行
        translated_text = argostranslate.translate.translate(original_text, "en", "ja")
        
        words_data = []
        for word in segment.words:
            words_data.append({
                "word": word.word.strip(),
                "start": word.start,
                "end": word.end
            })

        final_data.append({
            "start": segment.start,
            "end": segment.end,
            "text": original_text,
            "translation": translated_text,
            "words": words_data
        })

    # 4. ファイルの生成と移動
    # 動画を移動（ここでリネーム後の名前を使用）
    dest_video_path = os.path.join(output_dir, safe_filename)
    
    print(f"動画ファイルを移動中: {video_path} -> {dest_video_path}")
    try:
        shutil.move(video_path, dest_video_path)
    except Exception as e:
        print(f"ファイルの移動に失敗しました: {e}")
        print("処理を中断せず、データの保存を続行します（動画ファイルは手動で移動してください）。")

    # データファイルをJS形式で保存
    # JS内の videoFile 指定も safe_filename にする
    js_content = f"const MEDIA_DATA = {{\n  videoFile: '{safe_filename}',\n  segments: {json.dumps(final_data, ensure_ascii=False, indent=2)}\n}};"
    
    with open(os.path.join(output_dir, "data.js"), "w", encoding="utf-8") as f:
        f.write(js_content)

    # プレーヤーHTMLをテンプレートからコピー
    template_path = os.path.join("templates", "player_template.html")
    if os.path.exists(template_path):
        shutil.copy2(template_path, os.path.join(output_dir, "index.html"))
    else:
        print("警告: templates/player_template.html が見つかりませんでした。")

    print("処理完了！以下のフォルダを確認してください。")
    print(output_dir)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("エラー: 動画ファイルをドラッグ＆ドロップするか、パスを指定してください。")
    else:
        video_input = sys.argv[1]
        process_video(video_input)