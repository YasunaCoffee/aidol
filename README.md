# VOICEVOX 3人対話音声生成システム（動画作成対応）

このシステムは、VOICEVOXを使用して3人の話者による対話音声を生成・結合し、さらに字幕付き動画も作成できるPythonスクリプトです。

## 話者設定

現在の話者設定：
- **youchusu**: 九州そら（ID: 16）
- **nichan**: 猫使アル（ID: 55）
- **suzu**: 冥鳴ひまり（ID: 14）

## 必要な環境

1. **VOICEVOX**が起動していること（ポート50021）
2. 必要なPythonライブラリ：
   ```bash
   pip install -r requirements.txt
   ```
   または個別インストール：
   ```bash
   pip install requests pydub moviepy Pillow
   ```

## 使用方法

### 🎤 基本的な音声生成

```bash
python main.py takoyaki_script.txt
```

### 🎬 音声生成＋動画作成

```bash
python main.py takoyaki_script.txt --create-video
```

### 📹 既存音声から動画のみ作成

```bash
python main.py takoyaki_script.txt --video-only
```

### 🔗 音声結合のみ

```bash
python main.py takoyaki_script.txt --combine-only
```

## スクリプトファイルの書式

### パラメータありの場合
```
[話者名:パラメータ]テキスト内容
```

### パラメータなしの場合（シンプル）
```
[話者名]テキスト内容
```

## 🖼️ キャラクター画像について

- `images/`フォルダに各キャラクターの画像を配置してください：
  - `images/youchusu.png` - 九州そら用
  - `images/nichan.png` - 猫使アル用  
  - `images/suzu.png` - 冥鳴ひまり用

- 画像がない場合は、自動的にデフォルト画像（キャラクター名入りの色付き背景）が作成されます

## 出力ファイル

### 音声ファイル
- 個別音声: `podcasts/dialogue_XXX_話者名.wav`
- 結合音声: `podcasts/combined_dialogue_YYYYMMDD_HHMMSS.wav`

### 動画ファイル
- 字幕付き動画: `podcasts/video_YYYYMMDD_HHMMSS.mp4`

## ✨ 動画の特徴

- **1280x720 HD解像度**
- **キャラクター別画像表示**：音声の長さに応じて自動切り替え
- **字幕表示**：画面下部にキャラクター名付きで表示
- **24fps**で滑らかな再生

## サンプルファイル

- `takoyaki_script.txt` - パラメータ付き詳細スクリプト
- `takoyaki_kakko.txt` - シンプル形式のスクリプト

## トラブルシューティング

1. **VOICEVOXが起動していない場合**
   - VOICEVOXアプリケーションを起動してください
   - デフォルトポート50021で動作していることを確認してください

2. **動画作成でエラーが出る場合**
   - ffmpegがインストールされていることを確認してください
   - moviepyが正しくインストールされていることを確認してください

3. **フォントエラーが出る場合**
   - システムにTrueTypeフォントがインストールされていることを確認してください
   - Windowsの場合は通常問題ありません

4. **音声ファイルが見つからない場合**
   - まず音声生成（`--create-video`なし）を実行してから動画作成してください
   - または`--video-only`フラグを使わずに同時実行してください 