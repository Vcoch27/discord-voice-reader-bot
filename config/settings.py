import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

TOKEN_PLACEHOLDERS = {
    "YOUR_TOKEN_HERE",
    "your_discord_bot_token_here",
    "DISCORD_TOKEN=YOUR_TOKEN_HERE",
}


def _get_int(name: str, default: int, minimum: int = 1) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        value = int(raw_value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer.") from exc

    if value < minimum:
        raise RuntimeError(f"{name} must be greater than or equal to {minimum}.")

    return value


def _get_bool(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class Settings:
    discord_token: str = os.getenv("DISCORD_TOKEN", "")
    command_prefix: str = os.getenv("COMMAND_PREFIX", "!")
    ffmpeg_executable: str = os.getenv("FFMPEG_EXECUTABLE", "ffmpeg")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    tts_rate: str = os.getenv("TTS_RATE", "+0%")
    tts_volume: str = os.getenv("TTS_VOLUME", "+0%")
    tts_pitch: str = os.getenv("TTS_PITCH", "+0Hz")
    max_tts_chars: int = _get_int("MAX_TTS_CHARS", 200)
    max_queue_size: int = _get_int("MAX_QUEUE_SIZE", 3)
    tts_timeout_seconds: int = _get_int("TTS_TIMEOUT_SECONDS", 30)
    audio_temp_dir: Path = Path(os.getenv("AUDIO_TEMP_DIR", "/tmp/discord-tts"))
    cleanup_temp_on_start: bool = _get_bool("CLEANUP_TEMP_ON_START", True)
    discord_intents_minimal: bool = _get_bool("DISCORD_INTENTS_MINIMAL", True)


settings = Settings()


def validate_settings() -> None:
    if not settings.discord_token or settings.discord_token in TOKEN_PLACEHOLDERS:
        raise RuntimeError(
            "DISCORD_TOKEN is required. Set it locally in .env or in Northflank runtime variables."
        )
