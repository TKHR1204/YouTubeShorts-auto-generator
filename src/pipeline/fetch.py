"""
Topic fetching from RSS feeds and Google Trends.
"""
import time
import logging
from typing import Optional

import feedparser

log = logging.getLogger(__name__)


def fetch_rss_topics(feeds: list[str], max_per_feed: int = 5) -> list[dict]:
    topics = []
    for url in feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_per_feed]:
                title = entry.get("title", "").strip()
                summary = entry.get("summary", entry.get("description", "")).strip()
                if title:
                    topics.append({
                        "title": title,
                        "summary": summary[:200],
                        "source": "rss",
                        "url": entry.get("link", ""),
                    })
            log.info(f"RSS: {url} → {len(feed.entries[:max_per_feed])} items")
        except Exception as e:
            log.warning(f"RSS fetch failed for {url}: {e}")
    return topics


def fetch_trends_topics(geo: str = "JP", tz: int = 540) -> list[dict]:
    try:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl="ja-JP", tz=tz, timeout=(10, 25))
        time.sleep(1)  # avoid rate limit
        df = pytrends.trending_searches(pn="japan")
        topics = []
        for term in df[0].tolist()[:10]:
            if term:
                topics.append({
                    "title": str(term),
                    "summary": "Google Trendsのトレンドワード",
                    "source": "google_trends",
                    "url": "",
                })
        log.info(f"Google Trends: {len(topics)} topics")
        return topics
    except Exception as e:
        log.warning(f"Google Trends fetch failed: {e}")
        return []


def fetch_all_topics(
    feeds: Optional[list[str]] = None,
    include_trends: bool = True,
) -> list[dict]:
    from config import RSS_FEEDS, TRENDS_GEO, TRENDS_TZ

    all_topics: list[dict] = []

    rss_topics = fetch_rss_topics(feeds or RSS_FEEDS)
    all_topics.extend(rss_topics)

    if include_trends:
        trend_topics = fetch_trends_topics(geo=TRENDS_GEO, tz=TRENDS_TZ)
        all_topics.extend(trend_topics)

    # Deduplicate by title
    seen: set[str] = set()
    unique: list[dict] = []
    for t in all_topics:
        key = t["title"].lower()
        if key not in seen:
            seen.add(key)
            unique.append(t)

    log.info(f"Total unique topics: {len(unique)}")
    return unique
