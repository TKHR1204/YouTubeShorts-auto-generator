"""
YouTube Shorts uploader using YouTube Data API v3 + OAuth 2.0.

初回実行時: ブラウザが開いて Google ログイン → token.json に保存
2回目以降: token.json を自動ロード（再ログイン不要）

事前準備:
  1. Google Cloud Console でプロジェクト作成
  2. YouTube Data API v3 を有効化
  3. OAuth 2.0 クライアント ID を作成（デスクトップアプリ）
  4. client_secrets.json をダウンロードして yt_shorts/ 直下に置く
"""
import logging
import time
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

log = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
API_SERVICE = "youtube"
API_VERSION = "v3"

# Retry settings for resumable upload
MAX_RETRIES = 5
RETRIABLE_STATUS_CODES = {500, 502, 503, 504}


def _authenticate(client_secrets: Path, token_path: Path) -> Credentials:
    """Load or refresh OAuth 2.0 credentials."""
    creds: Credentials | None = None

    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        except Exception as e:
            log.warning(f"token.json の読み込みに失敗しました（削除して再認証します）: {e}")
            token_path.unlink(missing_ok=True)
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            log.info("OAuth トークンをリフレッシュしています...")
            try:
                creds.refresh(Request())
            except Exception as e:
                log.warning(f"トークンリフレッシュ失敗（再認証します）: {e}")
                token_path.unlink(missing_ok=True)
                creds = None

    if not creds or not creds.valid:
        if not client_secrets.exists():
            raise FileNotFoundError(
                f"client_secrets.json が見つかりません: {client_secrets}\n"
                "Google Cloud Console からダウンロードして yt_shorts/ に置いてください。"
            )
        log.info("ブラウザで Google 認証を行います...")
        flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets), SCOPES)
        creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json())
        log.info(f"認証情報を保存: {token_path}")

    return creds


def _build_service(client_secrets: Path, token_path: Path):
    creds = _authenticate(client_secrets, token_path)
    return build(API_SERVICE, API_VERSION, credentials=creds)


def _handle_401(e: HttpError):
    """Raise a clear error for 401 responses with actionable guidance."""
    import json as _json
    try:
        details = _json.loads(e.content.decode())
        errors = details.get("error", {}).get("errors", [{}])
        reason = errors[0].get("reason", "")
    except Exception:
        reason = ""

    if reason == "youtubeSignupRequired":
        raise RuntimeError(
            "アップロード失敗: 認証に使用した Google アカウントに YouTube チャンネルが存在しません。\n"
            "対処法:\n"
            "  1. https://www.youtube.com を開く\n"
            "  2. 同じ Google アカウントでログイン\n"
            "  3. 「チャンネルを作成」を完了させる\n"
            "  4. token.json を削除してから再実行する\n"
            f"     rm yt_shorts/token.json"
        ) from e

    raise RuntimeError(
        f"YouTube API 認証エラー (401): reason={reason!r}\n"
        "token.json を削除して再実行してください: rm yt_shorts/token.json"
    ) from e


def _upload_with_retry(request) -> str:
    """Execute resumable upload with exponential backoff."""
    response = None
    error = None
    retry = 0

    while response is None:
        try:
            log.info(f"アップロード中... (試行 {retry + 1})")
            status, response = request.next_chunk()
            if status:
                pct = int(status.progress() * 100)
                log.info(f"  進捗: {pct}%")
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = f"HTTP {e.resp.status}: {e}"
            elif e.resp.status == 401:
                _handle_401(e)
            else:
                raise
        except Exception as e:
            error = str(e)

        if error:
            retry += 1
            if retry > MAX_RETRIES:
                raise RuntimeError(f"アップロード失敗（最大リトライ超過）: {error}")
            wait = 2 ** retry
            log.warning(f"リトライ {retry}/{MAX_RETRIES}（{wait}秒後）: {error}")
            time.sleep(wait)
            error = None

    return response["id"]


def upload_video(
    video_path: Path,
    metadata: dict,
    client_secrets: Path,
    token_path: Path,
    privacy: str = "private",
) -> dict:
    """
    Upload video to YouTube.

    Args:
        video_path:      Path to the MP4 file
        metadata:        dict with title, description, tags, category_id
        client_secrets:  Path to client_secrets.json
        token_path:      Path to token.json (auto-created on first auth)
        privacy:         "public" | "unlisted" | "private"

    Returns:
        {"video_id": str, "url": str, "privacy": str}
    """
    # Shorts requires #Shorts in title or description
    description = metadata.get("description", "")
    if "#Shorts" not in description and "#shorts" not in description:
        description += "\n\n#Shorts"

    title = metadata.get("title", "YouTube Shorts")
    # YouTube title limit: 100 chars
    title = title[:100]

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": metadata.get("tags", []) + ["Shorts"],
            "categoryId": metadata.get("category_id", "22"),
            "defaultLanguage": metadata.get("default_language", "ja"),
            "defaultAudioLanguage": metadata.get("default_language", "ja"),
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    log.info(f"YouTube にアップロードします: {title}")
    log.info(f"  ファイル : {video_path}")
    log.info(f"  公開設定 : {privacy}")

    service = _build_service(client_secrets, token_path)
    media = MediaFileUpload(
        str(video_path),
        mimetype="video/mp4",
        resumable=True,
        chunksize=256 * 1024,  # 256 KB chunks
    )

    insert_request = service.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media,
    )

    video_id = _upload_with_retry(insert_request)
    url = f"https://www.youtube.com/shorts/{video_id}"

    log.info(f"アップロード完了!")
    log.info(f"  動画 ID : {video_id}")
    log.info(f"  URL     : {url}")

    return {"video_id": video_id, "url": url, "privacy": privacy}
