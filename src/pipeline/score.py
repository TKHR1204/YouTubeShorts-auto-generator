"""
AI-based topic scoring and selection via Claude.
"""
import logging

import anthropic

from pipeline.utils import parse_json_response

log = logging.getLogger(__name__)


def score_and_select_topics(
    topics: list[dict],
    client: anthropic.Anthropic,
    n: int = 1,
) -> list[dict]:
    """
    Score topics and return the top-N picks in ranked order.
    Uses a single Claude call regardless of N.
    """
    if not topics:
        raise ValueError("No topics to score")

    n = min(n, len(topics))
    # Limit candidates to keep prompt manageable
    candidates = topics[:30]
    numbered = "\n".join(
        f"{i+1}. [{t['source']}] {t['title']}"
        for i, t in enumerate(candidates)
    )

    prompt = f"""あなたはYouTube Shortsのコンテンツプランナーです。
以下のトピック候補を評価し、**YouTube Shortsに適した上位{n}つ**を重要度順に選んでください。

評価基準（重要度順）:
1. 視聴者が「おっ」と思う意外性・驚き
2. 60秒以内で完結するスケール感
3. 今のトレンドとの関連性
4. 幅広い日本人視聴者への訴求力

トピック候補:
{numbered}

以下のJSON形式のみで回答してください（説明不要、他のテキスト不要）:
{{
  "selected": [
    {{"index": 3}},
    {{"index": 7}},
    ...
  ]
}}
必ず{n}件選んでください。indexは1始まりの整数。重複は不可。"""

    log.info(f"Scoring topics with Claude (top {n})...")
    response = client.messages.create(
        model=__import__("config").CLAUDE_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    result = parse_json_response(raw)
    selected_list = result["selected"][:n]

    output = []
    for item in selected_list:
        idx = int(item["index"]) - 1
        if idx < 0 or idx >= len(candidates):
            log.warning(f"Invalid index {idx+1}, skipping")
            continue
        topic = dict(candidates[idx])
        log.info(f"  Selected: {topic['title']}")
        output.append(topic)

    if not output:
        raise ValueError("Claude returned no valid topic selections")
    return output


def score_and_select_topic(topics: list[dict], client: anthropic.Anthropic) -> dict:
    """Convenience wrapper: select exactly 1 topic."""
    return score_and_select_topics(topics, client, n=1)[0]
