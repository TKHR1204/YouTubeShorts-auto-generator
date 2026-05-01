"""
YouTube Shorts metadata generation (title, description, tags) via Claude.
"""
import logging

import anthropic

from pipeline.utils import parse_json_response

log = logging.getLogger(__name__)


def generate_metadata(topic: dict, script: dict, client: anthropic.Anthropic) -> dict:
    slides_summary = "\n".join(
        f"- [{s['type']}] {s['headline']}: {s['narration'][:60]}..."
        for s in script["slides"]
    )

    prompt = f"""あなたはYouTube Shortsのマーケターです。
以下の動画内容に対して、最適なメタデータを作成してください。

トピック: {topic['title']}
スライド構成:
{slides_summary}

要件:
- タイトル: 50文字以内、クリックしたくなる煽り気味のもの（数字や疑問形を活用）
- 説明文: 150文字以内、概要＋関連ハッシュタグ5〜8個
- タグ: 関連キーワード10個（リスト形式）
- カテゴリ: YouTube のカテゴリID（教育=27, エンタメ=24, ニュース=25 など）

以下のJSON形式**のみ**で出力:
{{
  "title": "タイトル",
  "description": "説明文\\n\\n#タグ1 #タグ2 #タグ3",
  "tags": ["タグ1", "タグ2", "タグ3"],
  "category_id": "27",
  "default_language": "ja"
}}"""

    log.info("Generating metadata with Claude...")
    response = client.messages.create(
        model=__import__("config").CLAUDE_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    metadata = parse_json_response(raw)
    log.info(f"Title: {metadata['title']}")
    return metadata
