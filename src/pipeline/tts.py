"""
Text-to-Speech generation.
Primary: gTTS (Google TTS, Japanese)
Fallback: silent MP3 via ffmpeg (dummy mode)
"""
import logging
import subprocess
from pathlib import Path

log = logging.getLogger(__name__)


def generate_tts(text: str, output_path: Path, lang: str = "ja") -> Path:
    """Generate TTS audio. Returns path to the MP3 file."""
    output_path = Path(output_path)

    try:
        from gtts import gTTS
        log.info(f"Generating TTS ({len(text)} chars) → {output_path.name}")
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(str(output_path))
        log.info("TTS generated successfully (gTTS)")
        return output_path
    except ImportError:
        log.warning("gTTS not installed, falling back to silent audio")
    except Exception as e:
        log.warning(f"gTTS failed ({e}), falling back to silent audio")

    # Fallback: generate 55s of silence
    return _generate_silence(output_path, duration=55)


def _generate_silence(output_path: Path, duration: int = 55) -> Path:
    """Create a silent MP3 using ffmpeg."""
    log.info(f"Generating {duration}s silent audio → {output_path.name}")
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"anullsrc=r=44100:cl=stereo",
            "-t", str(duration),
            "-c:a", "libmp3lame",
            "-b:a", "128k",
            str(output_path),
        ],
        check=True,
        capture_output=True,
    )
    return output_path
