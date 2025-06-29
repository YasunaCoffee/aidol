import asyncio
import requests
import json
import re
from pydub import AudioSegment
import os
from datetime import datetime
import argparse
import sys
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, TextClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont
import tempfile

# 話者IDの設定を更新（VOICEVOXの話者ID）
speaker_ids = {
    'youchusu': 16,     # 九州そら（ノーマル）
    'nichan': 55,      # 猫使アル（ノーマル）
    'suzu': 14      # 冥鳴ひまり（ノーマル）
}

# キャラクター画像の設定
character_images = {
    'youchusu': 'images/youchusu.png',  # 九州そら
    'nichan': 'images/nichan.png',      # 猫使アル
    'suzu': 'images/suzu.png'           # 冥鳴ひまり
}

def create_default_character_images():
    """デフォルトのキャラクター画像を作成"""
    os.makedirs('images', exist_ok=True)
    
    # 各キャラクターのデフォルト画像を作成
    character_colors = {
        'youchusu': '#FFB6C1',  # ライトピンク
        'nichan': '#98FB98',    # ペールグリーン  
        'suzu': '#87CEEB'       # スカイブルー
    }
    
    for character, color in character_colors.items():
        image_path = f'images/{character}.png'
        if not os.path.exists(image_path):
            # 720x720のキャラクター画像を作成
            img = Image.new('RGB', (720, 720), color)
            draw = ImageDraw.Draw(img)
            
            # キャラクター名を描画
            try:
                font = ImageFont.truetype("arial.ttf", 60)
            except:
                font = ImageFont.load_default()
            
            # テキストサイズを取得して中央に配置
            bbox = draw.textbbox((0, 0), character, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (720 - text_width) // 2
            y = (720 - text_height) // 2
            
            draw.text((x, y), character, fill='white', font=font)
            img.save(image_path)
            print(f"デフォルト画像を作成しました: {image_path}")

def get_audio_duration(audio_file_path):
    """音声ファイルの長さを取得（秒）"""
    try:
        audio = AudioSegment.from_wav(audio_file_path)
        return len(audio) / 1000.0  # ミリ秒を秒に変換
    except Exception as e:
        print(f"音声ファイルの長さ取得エラー: {e}")
        return 0

def create_subtitle_image(text, character, width=1280, height=100):
    """字幕画像を作成"""
    img = Image.new('RGBA', (width, height), (0, 0, 0, 180))  # 半透明の黒背景
    draw = ImageDraw.Draw(img)
    
    # 日本語対応フォントを設定
    font = None
    font_paths = [
        "C:/Windows/Fonts/msgothic.ttc",      # MS ゴシック
        "C:/Windows/Fonts/msmincho.ttc",      # MS 明朝
        "C:/Windows/Fonts/NotoSansCJK.ttc",   # Noto Sans CJK
        "C:/Windows/Fonts/YuGothM.ttc",       # 游ゴシック Medium
        "C:/Windows/Fonts/meiryo.ttc",        # メイリオ
    ]
    
    # 利用可能なフォントを試す
    for font_path in font_paths:
        try:
            font = ImageFont.truetype(font_path, 36)
            break
        except:
            continue
    
    # フォントが見つからない場合はデフォルトフォントを使用
    if font is None:
        try:
            font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
    
    # キャラクター名付きテキスト
    subtitle_text = f"{character}: {text}"
    
    # テキストサイズを取得して中央に配置
    try:
        bbox = draw.textbbox((0, 0), subtitle_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    except:
        # 古いPillowバージョン用のフォールバック
        text_width, text_height = draw.textsize(subtitle_text, font=font)
    
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    draw.text((x, y), subtitle_text, fill='white', font=font)
    
    return img

async def create_video_from_dialogues(dialogue_list):
    """対話リストから動画を作成"""
    print("動画作成を開始します...")
    
    # デフォルト画像を作成
    create_default_character_images()
    
    # 動画クリップのリストを作成
    video_clips = []
    current_time = 0
    
    for i, dialogue in enumerate(dialogue_list):
        speaker = dialogue['speaker']
        text = dialogue['text']
        audio_file = f'podcasts/dialogue_{i:03d}_{speaker}.wav'
        
        if not os.path.exists(audio_file):
            print(f"警告: 音声ファイル {audio_file} が見つかりません。スキップします。")
            continue
        
        # 音声の長さを取得
        duration = get_audio_duration(audio_file)
        if duration <= 0:
            continue
        
        # キャラクター画像を読み込み
        image_path = character_images.get(speaker, f'images/{speaker}.png')
        if not os.path.exists(image_path):
            print(f"警告: 画像ファイル {image_path} が見つかりません。デフォルト画像を使用します。")
            image_path = f'images/{speaker}.png'
        
        # 画像クリップを作成
        image_clip = ImageClip(image_path).set_duration(duration).resize((1280, 720))
        
        # 音声クリップを作成
        audio_clip = AudioFileClip(audio_file)
        
        # 字幕画像を作成
        subtitle_img = create_subtitle_image(text, speaker)
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            subtitle_img.save(tmp_file.name)
            subtitle_clip = ImageClip(tmp_file.name).set_duration(duration).set_position(('center', 'bottom'))
        
        # 画像と字幕を合成
        video_clip = CompositeVideoClip([
            image_clip,
            subtitle_clip
        ]).set_audio(audio_clip)
        
        video_clips.append(video_clip)
        current_time += duration
        
        print(f"クリップ {i+1}/{len(dialogue_list)} 作成完了 ({speaker}: {duration:.2f}秒)")
    
    if not video_clips:
        print("動画クリップが作成されませんでした。")
        return
    
    # 全てのクリップを結合
    print("動画クリップを結合しています...")
    final_video = concatenate_videoclips(video_clips)
    
    # 動画を保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"podcasts/video_{timestamp}.mp4"
    
    print("動画ファイルを出力しています...")
    final_video.write_videofile(
        output_filename,
        fps=24,
        codec='libx264',
        audio_codec='aac',
        temp_audiofile='temp-audio.m4a',
        remove_temp=True
    )
    
    print(f"動画作成完了: {output_filename}")
    print(f"総再生時間: {final_video.duration:.2f}秒")
    
    # 一時ファイルをクリーンアップ
    final_video.close()
    for clip in video_clips:
        clip.close()

def get_available_speakers():
    """利用可能な話者一覧を取得"""
    base_url = 'http://127.0.0.1:50021'
    try:
        response = requests.get(f'{base_url}/speakers')
        return response.json()
    except requests.exceptions.ConnectionError:
        print("エラー: VOICEVOXが起動していないかもしれません")
        return []

async def list_speakers():
    speakers = get_available_speakers()
    if not speakers:
        return
        
    for speaker in speakers:
        print(f"スピーカー情報:")
        print(json.dumps(speaker, indent=2, ensure_ascii=False))
        print("---")

# スピーカーIDを動的に取得して設定
async def setup_speaker_ids():
    speakers = get_available_speakers()
    speaker_ids = {}
    
    for speaker in speakers:
        name = speaker.get('name', '').lower()
        if '九州そら' in name or 'kyushu' in name:
            speaker_ids['youchusu'] = speaker.get('speaker_uuid', 16)
        elif '猫使アル' in name or 'nekomushi' in name:
            speaker_ids['nichan'] = speaker.get('speaker_uuid', 55)
        elif '冥鳴ひまり' in name or 'meimei' in name:
            speaker_ids['suzu'] = speaker.get('speaker_uuid', 14)
    
    return speaker_ids

def parse_voice_params(line):
    """音声パラメータを解析する"""
    params = {}
    
    # パラメータありの形式: [speaker:param1=value1;param2=value2]text
    match = re.match(r'\[(.*?):(.*?)\](.*)', line)
    if match:
        speaker = match.group(1)
        param_str = match.group(2)
        text = match.group(3)
        
        # パラメータの解析
        for param in param_str.split(';'):
            if '=' in param:
                key, value = param.split('=', 1)
                params[key.strip()] = float(value)
        
        return {
            'speaker': speaker,
            'params': params,
            'text': text.strip()
        }
    
    # パラメータなしの形式: [speaker]text
    match = re.match(r'\[(.*?)\](.*)', line)
    if match:
        speaker = match.group(1)
        text = match.group(2)
        
        return {
            'speaker': speaker,
            'params': {},  # 空のパラメータ辞書
            'text': text.strip()
        }
    
    return None

def read_script(file_path):
    """スクリプトファイルを読み込む"""
    script_lines = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 空行、メタデータ、コメント行、マークダウン記法をスキップ
                if (line and 
                    not line.startswith('<') and  # メタデータ
                    not line.startswith('#') and  # コメント行
                    not line.startswith('##') and  # マークダウン見出し
                    not line.startswith('-') and  # マークダウンリスト
                    not line.startswith('---')):  # マークダウン区切り線
                    
                    parsed = parse_voice_params(line)
                    if parsed:
                        script_lines.append(parsed)
        return script_lines
    except FileNotFoundError:
        print(f"エラー: {file_path} が見つかりません")
        return None
    except Exception as e:
        print(f"エラー: ファイル読み込み中に問題が発生しました - {str(e)}")
        return None

async def generate_speech(dialogue_list, speaker_ids):
    """VOICEVOXを使って音声を生成します"""
    base_url = 'http://127.0.0.1:50021'
    audio_query_url = f'{base_url}/audio_query'
    synthesis_url = f'{base_url}/synthesis'
    
    # podcastsフォルダを作成
    os.makedirs('podcasts', exist_ok=True)
    
    # 話者ごとの音声を別々に保存
    for i, dialogue in enumerate(dialogue_list):
        speaker = dialogue['speaker']
        text = dialogue['text']
        params = dialogue['params']
        speaker_id = speaker_ids[speaker]
        
        # audio_queryを取得
        query_response = requests.post(
            audio_query_url,
            params={
                'text': text,
                'speaker': speaker_id
            }
        )
        query_data = query_response.json()
        
        # パラメータの適用
        if 'speedScale' in params:
            query_data['speedScale'] = params['speedScale']
        if 'pitchScale' in params:
            query_data['pitchScale'] = params['pitchScale']
        if 'intonationScale' in params:
            query_data['intonationScale'] = params['intonationScale']
        if 'volumeScale' in params:
            query_data['volumeScale'] = params['volumeScale']
        
        # 音声合成
        synthesis_response = requests.post(
            synthesis_url,
            params={
                'speaker': speaker_id
            },
            json=query_data
        )
        
        # podcastsフォルダに保存
        with open(f'podcasts/dialogue_{i:03d}_{speaker}.wav', 'wb') as f:
            f.write(synthesis_response.content)
        
        await asyncio.sleep(0.1)

    print("音声生成が完了しました！")
    print("以下のファイルが生成されています：")
    for i, dialogue in enumerate(dialogue_list):
        print(f"podcasts/dialogue_{i:03d}_{dialogue['speaker']}.wav")

async def combine_audio_files(dialogue_list):
    """生成された音声ファイルを結合します"""
    combined = AudioSegment.empty()

    for i, dialogue in enumerate(dialogue_list):
        speaker = dialogue['speaker']
        filename = f'podcasts/dialogue_{i:03d}_{speaker}.wav'  

        # 音声ファイルを読み込んで結合
        try:
            audio = AudioSegment.from_wav(filename)
            combined += audio 
        except FileNotFoundError:
            print(f"警告: {filename} が見つかりません。スキップします。")
        except Exception as e:
            print(f"警告: {filename} の読み込み中にエラーが発生しました: {e}。スキップします。")


    # タイムスタンプを生成（YYYYMMDD_HHMMSS形式）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"podcasts/combined_dialogue_{timestamp}.wav"

    # 結合したファイルをpodcastsフォルダに保存
    if len(combined) > 0:
        combined.export(output_filename, format="wav")
        print(f"音声ファイルを結合しました: {output_filename}")
    else:
        print("結合する音声ファイルがありませんでした。")

def process_script(script_path):
    """スクリプトファイルを処理する関数"""
    if not os.path.exists(script_path):
        print(f"Error: ファイル '{script_path}' が見つかりません。")
        return
    
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # スクリプトの内容を表示
        print(f"=== スクリプト '{os.path.basename(script_path)}' の内容 ===")
        print(content)
        print("=" * 50)
        
    except Exception as e:
        print(f"Error: ファイルの読み込み中にエラーが発生しました: {str(e)}")

async def main():
    """メイン関数"""
    # コマンドライン引数のパーサーを作成
    parser = argparse.ArgumentParser(description="対話スクリプトから音声を生成・結合します。")
    parser.add_argument("script_path", help="処理対象のスクリプトファイルパス")
    parser.add_argument(
        "--combine-only",
        action="store_true",
        help="音声生成をスキップし、既存の音声ファイルを結合する処理のみを実行します。"
    )
    parser.add_argument(
        "--create-video",
        action="store_true",
        help="音声ファイルから字幕付き動画を作成します。"
    )
    parser.add_argument(
        "--video-only",
        action="store_true",
        help="音声生成をスキップし、既存の音声ファイルから動画のみを作成します。"
    )
    args = parser.parse_args()

    script_path = args.script_path

    # スクリプトの内容を表示 (常に実行)
    process_script(script_path)

    # スクリプトを解析して音声生成用のデータを作成
    dialogues = read_script(script_path)
    if not dialogues:
        print("スクリプトの解析に失敗しました。")
        return

    print(f"解析された対話数: {len(dialogues)}")

    # 動画のみ作成モード
    if args.video_only:
        print("既存の音声ファイルから動画を作成します...")
        await create_video_from_dialogues(dialogues)
        return

    # --combine-only フラグが指定されていない場合のみ音声生成を実行
    if not args.combine_only:
        print("音声生成を開始します...")
        # VOICEVOXの場合、話者IDを動的に取得することもできます
        # speaker_ids = await setup_speaker_ids() # 必要に応じてコメント解除
        await generate_speech(dialogues, speaker_ids) # speaker_ids はグローバル変数を使用

    # 音声ファイルを結合 (combine-onlyまたは通常実行時)
    if not args.create_video:
        print("音声ファイルを結合します...")
        await combine_audio_files(dialogues)

    # 動画作成
    if args.create_video:
        await create_video_from_dialogues(dialogues)

    print("処理が完了しました！")

if __name__ == "__main__":
    asyncio.run(main()) 