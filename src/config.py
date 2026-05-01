import os
from pathlib import Path

# --- API ---
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-6"

# --- Paths ---
BASE_DIR = Path(__file__).parent.parent  # src/ → repo root
OUTPUT_DIR = BASE_DIR / "output"

# macOS Hiragino → AppleGothic → fallback to default
FONT_CANDIDATES = [
    "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
    "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
    "/Library/Fonts/NotoSansJP-Regular.ttf",
    # Linux
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    # Windows
    "C:/Windows/Fonts/meiryo.ttc",
]

# --- Video ---
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 30
MAX_DURATION_SEC = 60
NUM_SLIDES = 6  # hook + 4 content + outro

# --- RSS Feeds (Japanese tech/news) ---
RSS_FEEDS = [
    "https://www3.nhk.or.jp/rss/news/cat0.xml",           # NHK top news
    "https://zenn.dev/feed",                                # Zenn tech
    "https://qiita.com/popular-items/feed",                 # Qiita popular
    "https://feed.infoq.com/jp",                            # InfoQ JP
]

# --- Google Trends ---
TRENDS_GEO = "JP"
TRENDS_LANG = "ja-JP"
TRENDS_TZ = 540  # JST

# --- Colors for slides ---
SLIDE_THEMES = [
    {"bg": (15, 23, 42),    "accent": (99, 102, 241),  "text": (248, 250, 252)},   # dark indigo
    {"bg": (7, 31, 26),     "accent": (52, 211, 153),  "text": (236, 253, 245)},   # dark emerald
    {"bg": (30, 10, 45),    "accent": (192, 132, 252),  "text": (250, 245, 255)},  # dark purple
    {"bg": (25, 18, 5),     "accent": (251, 191, 36),  "text": (255, 251, 235)},   # dark amber
    {"bg": (23, 10, 10),    "accent": (248, 113, 113), "text": (255, 241, 242)},   # dark rose
    {"bg": (5, 25, 40),     "accent": (56, 189, 248),  "text": (240, 249, 255)},   # dark sky
]
