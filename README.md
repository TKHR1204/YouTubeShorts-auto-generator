# shorts-autopilot

RSSフィードとGoogle Trendsからトレンドトピックを自動収集し、**Claude AI**で台本を生成、TTS音声＋スライド画像をffmpegで合成して**YouTube Shortsに自動投稿**するPythonツールです。

> **Pythonを触ったことがない方でもこのREADMEを上から順に読めば動かせます。**

---

## 目次

1. [このツールでできること](#このツールでできること)
2. [動作の仕組み](#動作の仕組み)
3. [必要なもの（事前確認）](#必要なもの事前確認)
4. [STEP 1 — リポジトリをダウンロード](#step-1--リポジトリをダウンロード)
5. [STEP 2 — Pythonのセットアップ](#step-2--pythonのセットアップ)
6. [STEP 3 — ffmpegのインストール](#step-3--ffmpegのインストール)
7. [STEP 4 — Anthropic APIキーの取得](#step-4--anthropic-apiキーの取得)
8. [STEP 5 — まず動かしてみる（動作確認）](#step-5--まず動かしてみる動作確認)
9. [STEP 6 — YouTube自動投稿の設定（任意）](#step-6--youtube自動投稿の設定任意)
10. [使い方まとめ](#使い方まとめ)
11. [出力ファイルの説明](#出力ファイルの説明)
12. [トラブルシューティング](#トラブルシューティング)
13. [料金の目安](#料金の目安)

---

## このツールでできること

| 機能 | 説明 |
|---|---|
| テーマ自動収集 | NHK・Zenn・Qiitaなど複数のRSSとGoogle Trendsから今旬なトピックを収集 |
| AIスコアリング | Claude AIがバズりやすさ・視聴者訴求力でトピックを評価して自動選定 |
| 台本生成 | 60秒以内のShorts台本（6スライド構成）をAIが自動生成 |
| TTS音声 | 日本語ナレーション音声を自動生成（gTTS使用） |
| スライド画像 | 1080×1920のカラースライドを自動生成 |
| 動画合成 | スライド＋音声を結合してmp4を出力 |
| メタデータ生成 | タイトル・説明文・ハッシュタグをAIが生成 |
| YouTube自動投稿 | YouTube Data API経由で自動アップロード（省略可） |
| 複数本同時生成 | `--count 5` で5本まとめて生成・投稿 |

---

## 動作の仕組み

```
①RSSフィード     ②AIスコアリング   ③台本生成
  Google Trends  →  トピック選定  →  6スライド構成
      ↓
④TTS音声生成   ⑤スライド画像生成   ⑥動画合成
  audio.mp3   →  slide_00〜05.png  →  final.mp4
      ↓
⑦メタデータ生成  ⑧YouTubeアップロード（任意）
  タイトル・説明  →  youtube.com/shorts/xxxxx
```

---

## 必要なもの（事前確認）

- **PC**: macOS / Windows（WSL推奨）/ Linux
- **Python**: 3.12以上
- **ffmpeg**: 動画合成に必須
- **インターネット接続**: TTS・AI・RSS取得に必要
- **Anthropic APIキー**: Claude AI使用のため（有料、[料金の目安](#料金の目安)参照）
- **Googleアカウント + YouTubeチャンネル**: 自動投稿する場合のみ

---

## STEP 1 — リポジトリをダウンロード

ターミナル（macOS: `ターミナル.app`、Windows: `PowerShell`）を開いて実行します。

```bash
git clone https://github.com/TKHR1204/shorts-autopilot.git
cd shorts-autopilot
```

> **gitがない場合**: GitHubページ右上の「Code」→「Download ZIP」でダウンロードして解凍してください。

---

## STEP 2 — Pythonのセットアップ

### Pythonのバージョン確認

```bash
python3 --version
```

`Python 3.12.x` 以上が表示されればOKです。表示されない場合は以下からインストールしてください。

- **macOS**: https://www.python.org/downloads/ からインストーラーをダウンロード
- **Windows**: Microsoft Store で「Python 3.12」を検索してインストール
- **Ubuntu/Debian**: `sudo apt install python3.12 python3.12-venv`

### 仮想環境の作成（推奨）

仮想環境を使うことで、このツールの依存パッケージがPCのPython環境に影響しません。

```bash
# 仮想環境を作成
python3 -m venv .venv

# 仮想環境を有効化（macOS / Linux）
source .venv/bin/activate

# 仮想環境を有効化（Windows PowerShell）
.venv\Scripts\Activate.ps1
```

有効化すると、コマンドの先頭に `(.venv)` と表示されます。

```bash
(.venv) $   ← これが表示されていればOK
```

> **注意**: ターミナルを閉じると仮想環境が無効になります。次回から使う際は毎回 `source .venv/bin/activate` を実行してください。

### パッケージのインストール

```bash
pip install -r requirements.txt
```

インストールには1〜2分かかります。最後に `Successfully installed ...` と表示されればOKです。

---

## STEP 3 — ffmpegのインストール

ffmpegは動画の合成に使うツールです。

### macOS

```bash
# Homebrewがない場合はまずインストール
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# ffmpegをインストール
brew install ffmpeg
```

### Windows

1. https://ffmpeg.org/download.html を開く
2. 「Windows builds from gyan.dev」をクリック
3. `ffmpeg-release-essentials.zip` をダウンロードして解凍
4. 解凍したフォルダ内の `bin` フォルダのパスを環境変数 `PATH` に追加

または **winget** を使う場合:
```powershell
winget install ffmpeg
```

### Ubuntu / Debian

```bash
sudo apt update && sudo apt install ffmpeg
```

### インストール確認

```bash
ffmpeg -version
```

バージョン情報が表示されればOKです。

---

## STEP 4 — Anthropic APIキーの取得

Claude AIを使うためのAPIキーを取得します。

### 1. アカウント作成

https://console.anthropic.com にアクセスして、アカウントを作成します。

### 2. クレジットの追加

APIは従量課金制です。**「Billing」→「Add credit」** からクレジットカードで入金します。
最低$5（約750円）から利用できます（[料金の目安](#料金の目安)参照）。

### 3. APIキーの発行

1. コンソール左メニューの **「API Keys」** をクリック
2. **「Create Key」** ボタンをクリック
3. キー名を入力（例: `shorts-autopilot`）して作成
4. 表示された `sk-ant-api03-...` をコピー（**この画面を閉じると二度と表示されません**）

### 4. APIキーを環境変数に設定

```bash
# macOS / Linux（ターミナルに直接貼る）
export ANTHROPIC_API_KEY="sk-ant-api03-ここにキーを貼る"

# 次回ターミナルを開いても使えるよう永続化する場合
echo 'export ANTHROPIC_API_KEY="sk-ant-api03-ここにキーを貼る"' >> ~/.zshrc
source ~/.zshrc
```

```powershell
# Windows PowerShell（セッション中のみ）
$env:ANTHROPIC_API_KEY = "sk-ant-api03-ここにキーを貼る"

# 永続化する場合
[System.Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", "sk-ant-api03-ここにキーを貼る", "User")
```

### 5. 設定確認

```bash
echo $ANTHROPIC_API_KEY
```

`sk-ant-api03-...` が表示されればOKです。

---

## STEP 5 — まず動かしてみる（動作確認）

**まず `--dry-run` モードで試してください。** このモードはAI呼び出しをスキップするのでAPIの料金がかかりません。

```bash
python main.py --dry-run
```

以下のようなログが流れて動画が生成されれば成功です。

```
12:00:00 [INFO] Dry-run モード: AI呼び出しをスキップします
12:00:01 [INFO] RSSとTrendsからトピック候補を取得しました
12:00:02 [INFO] Generating TTS (xxx chars) → audio.mp3
12:00:08 [INFO] Slide 1/6 → slide_00.png
  ...
12:00:15 [INFO] Running ffmpeg → final.mp4
12:00:18 [INFO] Video created: final.mp4 (1.2 MB)

══════════════════════════════════════════════════
  完了: 1/1 本
══════════════════════════════════════════════════
  [1] ✓ （トピック名）
       動画 : output/20260501_120000_.../final.mp4
══════════════════════════════════════════════════
```

`output/` フォルダに `final.mp4` が生成されていることを確認してください。

### 動作確認OKなら本番実行

```bash
python main.py
```

初回はRSSの取得・AIの台本生成などで2〜3分かかります。

---

## STEP 6 — YouTube自動投稿の設定（任意）

YouTube投稿は必須ではありません。生成した `final.mp4` を手動でアップロードすることもできます。

自動投稿を使う場合は、Google Cloud ConsoleでAPIの認証設定が必要です。

### 6-1. Google Cloudプロジェクトの作成

1. https://console.cloud.google.com を開く（Googleアカウントでログイン）
2. 画面上部のプロジェクト選択ドロップダウン → **「新しいプロジェクト」**
3. プロジェクト名を入力（例: `shorts-autopilot`）→ **「作成」**
4. 作成したプロジェクトを選択

### 6-2. YouTube Data API v3 を有効化

1. 左メニュー **「APIとサービス」→「ライブラリ」**
2. 検索ボックスに `YouTube Data API v3` と入力
3. 表示された「YouTube Data API v3」をクリック → **「有効にする」**

### 6-3. OAuth 同意画面の設定

1. 左メニュー **「APIとサービス」→「OAuth 同意画面」**
2. User Type: **「外部」** を選択 → **「作成」**
3. アプリ名（例: `shorts-autopilot`）とメールアドレスを入力 → **「保存して次へ」**
4. 「スコープ」画面はそのまま **「保存して次へ」**
5. 「テストユーザー」で **「+ ADD USERS」** → 自分のGmailアドレスを追加 → **「保存して次へ」**
6. **「ダッシュボードに戻る」**

> **テストユーザーに追加した理由**: 公開申請なしでも自分のアカウントだけ使えるようにするためです。

### 6-4. OAuthクライアントIDの作成

1. 左メニュー **「APIとサービス」→「認証情報」**
2. 上部 **「+ 認証情報を作成」→「OAuth クライアント ID」**
3. アプリケーションの種類: **「デスクトップアプリ」** を選択
4. 名前を入力（例: `shorts-autopilot-desktop`）→ **「作成」**
5. 表示されたダイアログで **「JSONをダウンロード」** をクリック
6. ダウンロードしたファイルを **`client_secrets.json`** にリネームして `yt_shorts/` フォルダに置く

```
shorts-autopilot/
├── client_secrets.json   ← ここに置く
├── main.py
...
```

### 6-5. YouTubeチャンネルの確認

投稿先のGoogleアカウントで https://www.youtube.com を開き、**YouTubeチャンネルが作成済み**であることを確認してください。チャンネルがないと投稿時にエラーになります。

### 6-6. 初回認証（ブラウザが開きます）

```bash
python main.py --upload --privacy private
```

初回のみブラウザが自動で開きます。

1. `client_secrets.json` に使ったGoogleアカウントでログイン
2. 「shorts-autopilotがGoogleアカウントへのアクセスを求めています」→ **「続行」**
3. ターミナルに戻ると自動的に処理が続行されます

認証情報は `token.json` に保存されるので、**2回目以降は自動でログイン**されます。

> `client_secrets.json` と `token.json` は `.gitignore` により**Gitには含まれません**。大切に保管してください。

---

## 使い方まとめ

```bash
# ──────────────────────────────────────────
# 基本
# ──────────────────────────────────────────

# 1本生成（トピックはAIが自動選定）
python main.py

# 5本まとめて生成
python main.py --count 5

# トピックを自分で指定して生成
python main.py --topic "日本のAI規制の最新動向"

# ──────────────────────────────────────────
# YouTubeアップロード
# ──────────────────────────────────────────

# 生成 + 非公開でアップロード（デフォルト・安全）
python main.py --upload

# 生成 + 限定公開でアップロード
python main.py --upload --privacy unlisted

# 生成 + 公開でアップロード
python main.py --upload --privacy public

# 5本生成して全部アップロード
python main.py --count 5 --upload --privacy private

# ──────────────────────────────────────────
# その他
# ──────────────────────────────────────────

# Google Trendsをスキップ（RSSのみ。Trendsが不安定なとき）
python main.py --no-trends

# AI呼び出しなしで動作確認（無料）
python main.py --dry-run

# 詳細なログを表示して実行
python main.py --verbose
```

### オプション一覧

| オプション | 短縮形 | デフォルト | 説明 |
|---|---|---|---|
| `--topic TOPIC` | `-t` | — | トピックを手動指定 |
| `--count N` | `-n` | `1` | 生成する動画の本数 |
| `--output-dir DIR` | `-o` | `./output` | 出力先ディレクトリ |
| `--no-trends` | — | False | Google Trendsをスキップ |
| `--upload` | `-u` | False | YouTube自動アップロード |
| `--privacy` | — | `private` | `private` / `unlisted` / `public` |
| `--dry-run` | — | False | AI呼び出しなし（動作確認用） |
| `--verbose` | `-v` | False | 詳細ログ表示 |

---

## 出力ファイルの説明

実行するたびに `output/` の中にフォルダが作成されます。

```
output/
└── 20260501_120000_トピック名/
    ├── script.json          # AIが生成した台本（スライドごとのテキスト）
    ├── audio.mp3            # TTSで生成したナレーション音声
    ├── slides/
    │   ├── slide_00.png     # フックスライド（最初の1枚）
    │   ├── slide_01.png     # コンテンツスライド
    │   ├── slide_02.png
    │   ├── slide_03.png
    │   ├── slide_04.png
    │   └── slide_05.png     # アウトロスライド（最後の1枚）
    ├── final.mp4            # 完成した動画（1080×1920）
    ├── metadata.json        # タイトル・説明文・タグ
    └── upload_result.json   # アップロードした場合のみ（YouTube動画URL）
```

---

## トラブルシューティング

### `ANTHROPIC_API_KEY が設定されていません` と表示される

APIキーが環境変数に設定されていません。

```bash
export ANTHROPIC_API_KEY="sk-ant-api03-..."
```

ターミナルを閉じると消えるので、永続化する場合は `~/.zshrc` に追記してください。

---

### `ffmpeg: command not found` と表示される

ffmpegがインストールされていないか、PATHが通っていません。

```bash
# macOS
brew install ffmpeg

# Ubuntu
sudo apt install ffmpeg
```

---

### `gTTS` の音声生成が失敗して無音になる

gTTSはインターネット接続が必要です。接続を確認してください。オフライン環境では自動的に無音MP3（55秒）が生成されます。

---

### Google Trendsの取得でエラーが出る

Googleのレート制限により一時的にブロックされることがあります。`--no-trends` オプションを使ってRSSのみで実行してください。

```bash
python main.py --no-trends
```

---

### YouTube投稿で `youtubeSignupRequired` エラー

投稿先のGoogleアカウントにYouTubeチャンネルが存在しません。

1. https://www.youtube.com を開く
2. `client_secrets.json` に使ったGoogleアカウントでログイン
3. 「チャンネルを作成」を完了させる
4. `token.json` を削除して再実行

```bash
rm token.json
python main.py --upload
```

---

### YouTube投稿で `401 Unauthorized` エラー（トークン切れ）

```bash
rm token.json
python main.py --upload
```

ブラウザが再度開くのでログインし直してください。

---

### 日本語のスライドテキストが文字化けする・豆腐（□）になる

日本語フォントが見つかっていません。`config.py` の `FONT_CANDIDATES` にインストール済みの日本語フォントのパスを追加してください。

```python
# config.py
FONT_CANDIDATES = [
    "/path/to/your/japanese/font.ttf",   # ← ここに追加
    ...
]
```

インストール済みフォントの確認:
```bash
# macOS
ls /System/Library/Fonts/ | grep -i hiragi

# Ubuntu
fc-list :lang=ja
```

---

### `json.decoder.JSONDecodeError` が出る

AIの返答からJSONの抽出に失敗しています。もう一度実行すると多くの場合は解決します。

```bash
python main.py   # 再実行
```

---

## 料金の目安

### Anthropic API（Claude）

動画1本あたりの目安（claude-sonnet-4-6使用）:

| 処理 | 呼び出し回数 | おおよその費用 |
|---|---|---|
| トピックスコアリング | 1回 | 〜$0.001 |
| 台本生成 | 1回 | 〜$0.003 |
| メタデータ生成 | 1回 | 〜$0.001 |
| **合計（1本）** | 3回 | **〜$0.005（約0.75円）** |

**5本生成しても約4円程度**です。月100本生成しても約75円の計算です。

### YouTube Data API

無料枠（1日10,000ユニット）内で通常利用できます。動画アップロード1回は1,600ユニット消費するため、**1日6本まで無料**です。

---

## ディレクトリ構成

```
shorts-autopilot/
├── main.py                  # CLIエントリーポイント（ここから実行）
├── requirements.txt         # Pythonパッケージ一覧
├── README.md
├── .gitignore
├── output/                  # 生成ファイル（Gitには含まれない）
└── src/                     # ソースコード
    ├── config.py            # 定数・RSS URL・フォント・カラーテーマ設定
    └── pipeline/
        ├── fetch.py         # RSSとGoogle Trendsからトピック収集
        ├── score.py         # Claude AIによるトピックスコアリング
        ├── script.py        # 60秒台本生成
        ├── tts.py           # TTS音声生成（gTTS）
        ├── slides.py        # スライド画像生成（Pillow）
        ├── video.py         # 動画合成（ffmpeg）
        ├── metadata.py      # タイトル・説明文・タグ生成
        ├── uploader.py      # YouTube Data API v3 アップロード
        └── utils.py         # JSONパーサーなど共通ユーティリティ
```

---

## ライセンス

MIT License
