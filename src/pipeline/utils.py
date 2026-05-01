"""
Shared utilities for pipeline modules.
"""
import json
import re
import logging

log = logging.getLogger(__name__)


def parse_json_response(raw: str) -> dict | list:
    """
    Robustly parse a JSON response from Claude.

    Handles:
    - Markdown code fences (```json ... ```)
    - Leading/trailing prose around the JSON
    - Trailing commas (common LLM mistake)
    """
    text = raw.strip()

    # 1. Strip code fences
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first line (```json or ```) and last ``` line
        inner = "\n".join(lines[1:])
        text = inner.rsplit("```", 1)[0].strip()

    # 2. Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 3. Extract the outermost {...} or [...] block
    for pattern in (r'\{[\s\S]*\}', r'\[[\s\S]*\]'):
        m = re.search(pattern, text)
        if m:
            candidate = m.group(0)
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                # Try removing trailing commas before } or ]
                cleaned = re.sub(r',\s*([}\]])', r'\1', candidate)
                try:
                    return json.loads(cleaned)
                except json.JSONDecodeError:
                    pass

    log.error(f"JSON parse failed. Raw response:\n{raw[:500]}")
    raise ValueError(f"Could not parse JSON from Claude response: {raw[:200]!r}")
