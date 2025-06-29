# VOICEVOX 3人対話音声生成システム

このシステムは、VOICEVOXを使用して3人の話者による対話音声を生成・結合するPythonスクリプトです。

## 話者設定

現在の話者設定：
- **youchusu**: 九州そら（ID: 16）
- **nichan**: 猫使アル（ID: 55）
- **suzu**: 冥鳴ひまり（ID: 14）

## 必要な環境

1. **VOICEVOX**が起動していること（ポート50021）
2. 必要なPythonライブラリ：
   ```bash
   pip install requests pydub
   ```

## 使用方法

### 基本的な使用

```bash
python main.py sample_3speakers.txt
```

### 音声生成のみスキップして結合のみ実行

```bash
python main.py sample_3speakers.txt --combine-only
```

## スクリプトファイルの書式

```
[話者名:パラメータ]テキスト内容
```

### 例
```
[youchusu]こんにちは！
[nichan]はじめまして〜！
[suzu]よろしくお願いします。
```

## 出力ファイル

- 個別音声: `podcasts/dialogue_XXX_話者名.wav`
- 結合音声: `podcasts/combined_dialogue_YYYYMMDD_HHMMSS.wav`

## サンプルファイル

`sample_3speakers.txt`には3人の話者によるサンプル対話が含まれています。

## トラブルシューティング

1. **VOICEVOXが起動していない場合**
   - VOICEVOXアプリケーションを起動してください
   - デフォルトポート50021で動作していることを確認してください

2. **話者IDが見つからない場合**
   - `main.py`内の`speaker_ids`辞書を確認・更新してください
   - または`setup_speaker_ids()`関数を有効にして動的取得を使用してください

3. **音声ファイルが生成されない場合**
   - VOICEVOXの話者がインストールされていることを確認してください
   - ネットワーク接続とポート50021へのアクセスを確認してください 