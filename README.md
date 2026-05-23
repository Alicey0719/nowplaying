# NowPlaying

Windows で再生中の曲を取得して X (Twitter) に #nowplaying ポストするための補助ツールです。

![screenshot](assets/screenshot.png)

## 機能

- Windows Media Session API で再生中の曲情報（タイトル・アーティスト・アルバム・アートワーク）を自動取得
- Apple Music・Spotify・その他 SMTC 対応プレイヤーに対応
- アートワークをアップロードして Twitter Card として表示
- ツイート文言のテンプレートをカスタマイズ可能
- 5秒ごとに自動更新（手動更新も可能）

## インストール

1. [Releases](../../releases/latest) から `NowPlaying.zip` をダウンロード
2. 任意のフォルダに展開
3. `NowPlaying.exe` を起動

インストール不要です。設定は `%APPDATA%\NowPlaying\settings.json` に保存されます。

> **Note**  
> 初回起動時に Windows Defender SmartScreen の警告が出る場合があります。「詳細情報」→「実行」で起動できます。

## 使い方

### 基本操作

| ボタン | 機能 |
|--------|------|
| 𝕏 | ツイート画面を開く（テキスト・画像URLを自動入力） |
| 📋 | ツイートテキストをクリップボードにコピー |
| 🖼 | アートワークをクリップボードにコピー |
| ↺ | 曲情報を手動更新 |
| ⚙ | 設定画面を開く |
| トグルスイッチ | 自動更新のオン/オフ |

### ツイートテンプレート

設定画面からツイートの文言をカスタマイズできます。使用できるプレースホルダー：

- `{title}` — 曲名
- `{artist}` — アーティスト名
- `{album}` — アルバム名

デフォルト：
```
Now Playing: {title} - {artist} #nowplaying
```

## 動作要件

- Windows 11
- SMTC (System Media Transport Controls) に対応したプレイヤー
  - Apple Music、Spotify、Windows Media Player など

## 開発者向け

### 環境構築

```powershell
pip install -r requirements.txt
python nowplay.pyw
```

### ビルド

```powershell
python make_icon.py
pyinstaller nowplay.spec --clean --noconfirm
```

### リリース

`v*` タグをプッシュすると GitHub Actions が自動でビルド・リリースします。

```powershell
git tag v[version]
git push origin v[version]
```

### Twitter Card (Cloudflare Worker)

アートワーク画像を Twitter Card として表示するための Cloudflare Worker が `worker/` に含まれています。
