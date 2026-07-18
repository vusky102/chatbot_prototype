"""Edge TTS helpers shared by CLI (`main.py`) and Streamlit chat UI."""

from __future__ import annotations

import os
import platform
import subprocess
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

VIETNAMESE_DIACRITICS = set(
    "àáạảãâầấậẩẫăằắặẳẵ"
    "èéẹẻẽêềếệểễ"
    "ìíịỉĩ"
    "òóọỏõôồốộổỗơờớợởỡ"
    "ùúụủũưừứựửữ"
    "ỳýỵỷỹđ"
    "ÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ"
    "ÈÉẸẺẼÊỀẾỆỂỄ"
    "ÌÍỊỈĨ"
    "ÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠ"
    "ÙÚỤỦŨƯỪỨỰỬỮ"
    "ỲÝỴỶỸĐ"
)

LANGDETECT_CODES = {
    "en": "eng",
    "eng": "eng",
    "vi": "vie",
    "vie": "vie",
}


def get_bool_env(name: str, default: bool = False) -> bool:
    """Parse a boolean environment variable (`1`/`true`/`yes`/`on`)."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def normalize_language(language: str | None) -> str | None:
    """Normalize language labels to `eng` / `vie`, or None if unknown."""
    if not language:
        return None

    normalized = language.strip().lower()
    if normalized in {"en", "eng", "english"}:
        return "eng"
    if normalized in {"vi", "vie", "vietnamese", "tiếng việt"}:
        return "vie"
    return None


def detect_text_language(text: str, default_language: str) -> str:
    """Detect `eng`/`vie` from diacritics or langdetect; else `default_language`."""
    if any(character in VIETNAMESE_DIACRITICS for character in text):
        return "vie"

    try:
        from langdetect import DetectorFactory, detect_langs
    except ImportError:
        return default_language

    try:
        DetectorFactory.seed = 0
        candidates = detect_langs(text)
    except Exception:
        return default_language

    if not candidates:
        return default_language

    candidate = candidates[0]
    language = LANGDETECT_CODES.get(candidate.lang)
    if language and candidate.prob >= 0.70:
        return language

    return default_language


class TextToSpeechRouter:
    """Synthesize speech with edge-tts and optionally play it locally (CLI)."""

    VOICES = {
        "eng": (
            {"name": "en-US-AriaNeural", "gender": "Female"},
            {"name": "en-US-JennyNeural", "gender": "Female"},
            {"name": "en-US-GuyNeural", "gender": "Male"},
            {"name": "en-US-ChristopherNeural", "gender": "Male"},
        ),
        "vie": (
            {"name": "vi-VN-HoaiMyNeural", "gender": "Female"},
            {"name": "vi-VN-NamMinhNeural", "gender": "Male"},
        ),
    }

    def __init__(self) -> None:
        """Load TTS settings from environment variables."""
        self.enabled = get_bool_env("TTS_ENABLED", default=False)
        self.autoplay = get_bool_env("TTS_AUTOPLAY", default=True)
        self.default_language = (
            normalize_language(os.getenv("TTS_DEFAULT_LANGUAGE", "eng")) or "eng"
        )
        self.audio_dir = Path(os.getenv("TTS_AUDIO_DIR", "generated_audio"))
        self.voice_positions = {
            "eng": self.get_voice_position("eng"),
            "vie": self.get_voice_position("vie"),
        }

    def get_voice_position(self, language: str) -> int:
        """Read `TTS_VOICE_POSITION_{LANG}` and clamp to a valid voice index."""
        env_name = f"TTS_VOICE_POSITION_{language.upper()}"
        raw_position = os.getenv(env_name, "0")

        try:
            position = int(raw_position)
        except ValueError:
            print(f"TTS warning: {env_name} must be an integer; using 0")
            return 0

        if not 0 <= position < len(self.VOICES[language]):
            print(f"TTS warning: {env_name}={position} is out of range; using 0")
            return 0

        return position

    def get_voice(self, language: str) -> str:
        """Return the configured Neural voice name for a language."""
        position = self.voice_positions[language]
        return self.VOICES[language][position]["name"]

    def resolve_language(self, text: str) -> str:
        """Pick a supported TTS language for the given text."""
        language = detect_text_language(text, self.default_language)
        if language not in self.VOICES:
            return self.default_language
        return language

    def synthesize(self, text: str, language: str | None = None) -> Path:
        """Generate an mp3 file for `text` and return its path."""
        import edge_tts

        cleaned = (text or "").strip()
        if not cleaned:
            raise ValueError("No text to synthesize")

        selected = language or self.resolve_language(cleaned)
        if selected not in self.VOICES:
            selected = self.default_language

        self.audio_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        output_path = self.audio_dir / f"assistant_{timestamp}_{selected}.mp3"
        communicate = edge_tts.Communicate(cleaned, self.get_voice(selected))
        communicate.save_sync(str(output_path))
        return output_path

    def speak(self, text: str) -> Path | None:
        """CLI path: synthesize when TTS_ENABLED, optionally local-play."""
        if not self.enabled or not (text or "").strip():
            return None

        try:
            output_path = self.synthesize(text)
            if self.autoplay:
                self.play(output_path)
            return output_path
        except Exception as error:
            print(f"TTS warning: {error}")
            return None

    def play(self, output_path: Path | str) -> None:
        """Play an mp3 on the local machine (macOS/Windows helpers)."""
        path = str(output_path)
        system = platform.system()

        try:
            if system == "Darwin":
                subprocess.run(["afplay", path], check=True)
                return

            if system == "Windows":
                try:
                    import ctypes

                    path_str = str(Path(path).resolve())
                    ctypes.windll.winmm.mciSendStringW(
                        f'open "{path_str}" type mpegvideo alias mymp3',
                        None,
                        0,
                        0,
                    )
                    ctypes.windll.winmm.mciSendStringW("play mymp3 wait", None, 0, 0)
                    ctypes.windll.winmm.mciSendStringW("close mymp3", None, 0, 0)
                except Exception:
                    try:
                        import winsound

                        winsound.PlaySound(path, winsound.SND_FILENAME)
                    except Exception:
                        os.startfile(path)
                return

            print(f"TTS audio saved: {output_path}")
        except Exception as error:
            print(f"TTS audio saved: {output_path}")
            print(f"TTS playback warning: {error}")
