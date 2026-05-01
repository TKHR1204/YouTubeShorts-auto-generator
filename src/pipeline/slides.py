"""
Slide image generation using Pillow.
Output: 1080x1920 PNG per slide.
"""
import logging
import textwrap
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

log = logging.getLogger(__name__)


def _find_font(size: int) -> ImageFont.FreeTypeFont:
    """Find the best available font for Japanese text."""
    from config import FONT_CANDIDATES
    for path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    log.warning("No TrueType font found, using Pillow default (Japanese may not render)")
    return ImageFont.load_default()


def _draw_gradient_bg(draw: ImageDraw.ImageDraw, width: int, height: int, color_top: tuple, color_bottom: tuple):
    """Simple vertical gradient."""
    for y in range(height):
        ratio = y / height
        r = int(color_top[0] * (1 - ratio) + color_bottom[0] * ratio)
        g = int(color_top[1] * (1 - ratio) + color_bottom[1] * ratio)
        b = int(color_top[2] * (1 - ratio) + color_bottom[2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))


def _draw_multiline_centered(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    color: tuple,
    center_x: int,
    center_y: int,
    max_width_px: int,
    line_spacing: int = 8,
):
    """Draw centered, word-wrapped text."""
    # Wrap text to fit width
    avg_char_width = font.getbbox("あ")[2]
    max_chars = max(1, max_width_px // avg_char_width)
    lines = textwrap.wrap(text, width=max_chars)
    if not lines:
        return

    line_height = font.getbbox("あ")[3] + line_spacing
    total_height = line_height * len(lines)
    y = center_y - total_height // 2

    for line in lines:
        bbox = font.getbbox(line)
        text_width = bbox[2] - bbox[0]
        x = center_x - text_width // 2
        # Shadow
        draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0, 120))
        draw.text((x, y), line, font=font, fill=color)
        y += line_height


def generate_slide(
    slide: dict,
    output_path: Path,
    slide_num: int,
    total_slides: int,
    theme: dict,
    topic_title: str,
    width: int = 1080,
    height: int = 1920,
) -> Path:
    img = Image.new("RGB", (width, height), color=theme["bg"])
    draw = ImageDraw.Draw(img)

    # Gradient background (lighten slightly toward center)
    bg_top = tuple(min(255, c + 15) for c in theme["bg"])
    _draw_gradient_bg(draw, width, height, bg_top, theme["bg"])

    # Decorative accent bar at top
    bar_h = 12
    draw.rectangle([0, 0, width, bar_h], fill=theme["accent"])

    # Slide counter dots at bottom
    dot_r = 10
    dot_spacing = 30
    total_dots_w = total_slides * (dot_r * 2 + dot_spacing) - dot_spacing
    dot_x = (width - total_dots_w) // 2
    dot_y = height - 80
    for i in range(total_slides):
        fill = theme["accent"] if i == slide_num else (*theme["accent"][:3], 60)
        if isinstance(fill, tuple) and len(fill) == 3:
            draw.ellipse(
                [dot_x, dot_y - dot_r, dot_x + dot_r * 2, dot_y + dot_r],
                fill=fill if i == slide_num else theme["bg"],
                outline=theme["accent"],
                width=2,
            )
        dot_x += dot_r * 2 + dot_spacing

    slide_type = slide.get("type", "content")

    if slide_type == "hook":
        # Large emoji/icon placeholder at top third
        icon_font = _find_font(180)
        icon_text = "⚡"
        icon_bbox = icon_font.getbbox(icon_text)
        ix = (width - (icon_bbox[2] - icon_bbox[0])) // 2
        draw.text((ix, height // 6), icon_text, font=icon_font, fill=theme["accent"])

        # Headline (large)
        headline_font = _find_font(72)
        _draw_multiline_centered(
            draw, slide["headline"], headline_font, theme["text"],
            width // 2, height // 2 - 40, int(width * 0.85), line_spacing=12,
        )

        # "知ってた？" label
        label_font = _find_font(40)
        label = "知ってた？"
        lb = label_font.getbbox(label)
        draw.text(
            ((width - lb[2]) // 2, height // 2 + 80),
            label, font=label_font, fill=theme["accent"],
        )

    elif slide_type == "outro":
        # CTA slide
        outro_icon_font = _find_font(160)
        icon = "👍"
        ib = outro_icon_font.getbbox(icon)
        draw.text(((width - ib[2]) // 2, height // 5), icon, font=outro_icon_font, fill=theme["accent"])

        headline_font = _find_font(68)
        _draw_multiline_centered(
            draw, slide["headline"], headline_font, theme["text"],
            width // 2, height // 2 - 20, int(width * 0.85), line_spacing=10,
        )

        cta_font = _find_font(44)
        cta_lines = ["フォロー & いいね", "もっと見たい方はチャンネル登録!"]
        cy = height // 2 + 100
        for line in cta_lines:
            lb = cta_font.getbbox(line)
            draw.text(((width - lb[2]) // 2, cy), line, font=cta_font, fill=theme["accent"])
            cy += 60

    else:
        # Content slide
        # Slide number label (top area)
        num_font = _find_font(38)
        num_text = f"ポイント {slide_num}"
        nb = num_font.getbbox(num_text)
        draw.text((60, 60), num_text, font=num_font, fill=theme["accent"])

        # Accent line under number
        draw.rectangle([60, 105, 60 + nb[2], 110], fill=theme["accent"])

        # Headline (center-upper area)
        headline_font = _find_font(76)
        _draw_multiline_centered(
            draw, slide["headline"], headline_font, theme["text"],
            width // 2, height // 3, int(width * 0.85), line_spacing=14,
        )

        # Divider
        pad = 80
        draw.rectangle(
            [pad, height // 2 - 4, width - pad, height // 2 + 4],
            fill=(*theme["accent"][:3],),
        )

        # Body text (smaller, center-lower area)
        body_font = _find_font(44)
        body_text = slide.get("narration", "")
        _draw_multiline_centered(
            draw, body_text, body_font, theme["text"],
            width // 2, int(height * 0.65), int(width * 0.8), line_spacing=10,
        )

    # Topic watermark at bottom
    wm_font = _find_font(28)
    wm = f"#{topic_title[:15]}"
    wm_bbox = wm_font.getbbox(wm)
    draw.text(
        (width - wm_bbox[2] - 30, height - 50),
        wm, font=wm_font, fill=(*theme["accent"][:3],),
    )

    img.save(str(output_path), "PNG")
    return output_path


def generate_slides(script: dict, output_dir: Path, width: int = 1080, height: int = 1920) -> list[Path]:
    from config import SLIDE_THEMES
    slides_data = script["slides"]
    total = len(slides_data)
    paths = []

    for i, slide in enumerate(slides_data):
        theme = SLIDE_THEMES[i % len(SLIDE_THEMES)]
        out = output_dir / f"slide_{i:02d}.png"
        generate_slide(
            slide=slide,
            output_path=out,
            slide_num=i,
            total_slides=total,
            theme=theme,
            topic_title=script.get("topic_title", ""),
            width=width,
            height=height,
        )
        log.info(f"Slide {i+1}/{total} → {out.name}")
        paths.append(out)

    return paths
