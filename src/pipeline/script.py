"""
60-second Shorts script generation via Claude.
"""
import logging

import anthropic

from pipeline.utils import parse_json_response

log = logging.getLogger(__name__)

SLIDE_TYPES = ["hook", "content", "content", "content", "content", "outro"]


def generate_script(topic: dict, client: anthropic.Anthropic, num_slides: int = 6) -> dict:
    """
    Returns:
        {
            "topic_title": str,
            "slides": [
                {"type": "hook"|"content"|"outro", "headline": str, "narration": str, "duration": int},
                ...
            ],
            "full_narration": str,
        }
    """
    slide_descriptions = (
        "1枚目: フック（視聴者を引き込む衝撃的な一言、疑問形）\n"
        "2〜5枚目: メインコンテンツ（各スライドに1つのポイント、具体的な数字や事実を含める）\n"
        "6枚目: アウトロ（まとめ＋「フォロー＆いいね」を促す一言）"
    )

    prompt = f"""あなたはバイラルYouTube Shortsの脚本家です。
以下のトピックで**60秒以内**のShorts動画の脚本を作成してください。

トピック: {topic['title']}
補足情報: {topic.get('summary', 'なし')}

スライド構成（全{num_slides}枚）:
{slide_descriptions}

ナレーションの注意点:
- 全体で60秒以内（ゆっくり読んで）
- テンポよく、短い文を積み重ねる
- 最初の5秒で興味を掴む
- 専門用語は避け、中学生でもわかる言葉で

以下のJSON形式**のみ**で出力してください:
{{
  "topic_title": "{topic['title']}",
  "slides": [
    {{
      "type": "hook",
      "headline": "スライドに表示する短い見出し（20文字以内）",
      "narration": "このスライドのナレーション（話す内容）",
      "duration": 8
    }},
    {{
      "type": "content",
      "headline": "見出し",
      "narration": "ナレーション",
      "duration": 10
    }},
    {{
      "type": "content",
      "headline": "見出し",
      "narration": "ナレーション",
      "duration": 10
    }},
    {{
      "type": "content",
      "headline": "見出し",
      "narration": "ナレーション",
      "duration": 10
    }},
    {{
      "type": "content",
      "headline": "見出し",
      "narration": "ナレーション",
      "duration": 10
    }},
    {{
      "type": "outro",
      "headline": "まとめ",
      "narration": "ナレーション",
      "duration": 8
    }}
  ]
}}"""

    log.info("Generating script with Claude...")
    response = client.messages.create(
        model=__import__("config").CLAUDE_MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    data = parse_json_response(raw)

    # Build full narration for TTS
    full_narration = " ".join(s["narration"] for s in data["slides"])
    data["full_narration"] = full_narration

    log.info(f"Script generated: {len(data['slides'])} slides, {len(full_narration)} chars")
    return data
