"""
Video assembly via ffmpeg.
Creates 1080x1920 MP4 from slide images + audio.
"""
import logging
import subprocess
import tempfile
from pathlib import Path

log = logging.getLogger(__name__)


def _get_audio_duration(audio_path: Path) -> float:
    """Use ffprobe to get audio duration in seconds."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_path),
        ],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


def _write_concat_file(slide_paths: list[Path], duration_each: float, tmp_file: Path):
    """Write ffmpeg concat demuxer input file."""
    lines = []
    for path in slide_paths:
        lines.append(f"file '{path.resolve()}'")
        lines.append(f"duration {duration_each:.3f}")
    # ffmpeg quirk: repeat last file without duration to avoid 1-frame truncation
    lines.append(f"file '{slide_paths[-1].resolve()}'")
    tmp_file.write_text("\n".join(lines))


def create_video(
    slide_paths: list[Path],
    audio_path: Path,
    output_path: Path,
    width: int = 1080,
    height: int = 1920,
    fps: int = 30,
    crf: int = 23,
) -> Path:
    if not slide_paths:
        raise ValueError("No slide images provided")

    audio_duration = _get_audio_duration(audio_path)
    # Cap at 60s for Shorts compliance
    effective_duration = min(audio_duration, 60.0)
    duration_each = effective_duration / len(slide_paths)

    log.info(
        f"Video: {len(slide_paths)} slides × {duration_each:.1f}s = {effective_duration:.1f}s"
    )

    concat_file = output_path.parent / "concat.txt"
    _write_concat_file(slide_paths, duration_each, concat_file)

    # Scale + pad to exact 1080x1920, yuv420p for wide compatibility
    vf = (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,"
        f"format=yuv420p"
    )

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_file),
        "-i", str(audio_path),
        "-vf", vf,
        "-r", str(fps),
        "-c:v", "libx264", "-preset", "fast", "-crf", str(crf),
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        "-t", str(effective_duration),
        str(output_path),
    ]

    log.info(f"Running ffmpeg → {output_path.name}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log.error(f"ffmpeg stderr:\n{result.stderr[-2000:]}")
        raise RuntimeError(f"ffmpeg failed (exit {result.returncode})")

    size_mb = output_path.stat().st_size / 1_048_576
    log.info(f"Video created: {output_path.name} ({size_mb:.1f} MB)")
    return output_path
