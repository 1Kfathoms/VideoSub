# 仕様:
# 1. 動画ファイルを入力として受け取る
# 2. stable-ts (Whisper) で単語レベルのタイムスタンプ付き文字起こしを実行 (GPU使用)
# 3. argostranslate でセグメントごとに翻訳
# 4. outputフォルダを作成（フォルダ名は元のファイル名を維持）
# 5. 動画ファイルを「video.[拡張子]」にリネームして出力フォルダへ移動し、data.js と index.html を生成する
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
        argostranslate.package.install_from_path(package_to_install.download())
        print("翻訳モデルをロードしました。")
    else:
        print("翻訳モデルが見つかりませんでした。")

def process_video(video_path):
    # パス設定
    filename = os.path.basename(video_path)
    name_without_ext = os.path.splitext(filename)[0]
    ext = os.path.splitext(filename)[1].lower() # 拡張子取得 (.mp4など)
    
    # フォルダ名は元のファイル名を使用
    output_dir = os.path.join("output", name_without_ext)
    
    # 保存する動画ファイル名は固定 (video.mp4 等)
    safe_video_filename = f"video{ext}"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"処理開始: {filename}")
    print(f"出力フォルダ: {output_dir}")
    print(f"保存ファイル名: {safe_video_filename}")

    # 1. GPUチェックとWhisperモデルロード
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")
    
    # モデルロード
    model = stable_whisper.load_model("large-v3", device=device)

    # 2. 文字起こし実行 (stable-ts)
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
    dest_video_path = os.path.join(output_dir, safe_video_filename)
    
    print(f"動画ファイルを移動中: {video_path} -> {dest_video_path}")
    try:
        shutil.move(video_path, dest_video_path)
    except Exception as e:
        print(f"ファイルの移動に失敗しました: {e}")
        print("処理を中断せず、データの保存を続行します（動画ファイルは手動で移動してください）。")

    # データファイルをJS形式で保存
    # originalFileNameを追加、videoFileは固定名を使用
    # JSONダンプ時にエスケープ処理を行う
    js_data_obj = {
        "videoFile": safe_video_filename,
        "originalFileName": filename,
        "segments": final_data
    }
    
    js_content = f"const MEDIA_DATA = {json.dumps(js_data_obj, ensure_ascii=False, indent=2)};"
    
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