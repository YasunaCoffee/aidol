import asyncio
import requests
import json
import re
from pydub import AudioSegment
import os
from datetime import datetime
import argparse
import sys

# 話者IDの設定を更新（VOICEVOXの話者ID）
speaker_ids = {
    'youchusu': 16,     # 九州そら（ノーマル）
    'nichan': 55,      # 猫使アル（ノーマル）
    'suzu': 14      # 冥鳴ひまり（ノーマル）
}

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
        action="store_true", # このフラグが指定されたら True になる
        help="音声生成をスキップし、既存の音声ファイルを結合する処理のみを実行します。"
    )
    args = parser.parse_args() # 引数を解析

    script_path = args.script_path

    # スクリプトの内容を表示 (常に実行)
    process_script(script_path)

    # スクリプトを解析して音声生成用のデータを作成
    dialogues = read_script(script_path)
    if not dialogues:
        print("スクリプトの解析に失敗しました。")
        return

    print(f"解析された対話数: {len(dialogues)}")

    # --combine-only フラグが指定されていない場合のみ音声生成を実行
    if not args.combine_only:
        print("音声生成を開始します...")
        # VOICEVOXの場合、話者IDを動的に取得することもできます
        # speaker_ids = await setup_speaker_ids() # 必要に応じてコメント解除
        await generate_speech(dialogues, speaker_ids) # speaker_ids はグローバル変数を使用

    # 音声ファイルを結合 (常に実行、ただしファイルがない場合は警告が出る)
    print("音声ファイルを結合します...")
    await combine_audio_files(dialogues)

    print("処理が完了しました！")

if __name__ == "__main__":
    asyncio.run(main()) 