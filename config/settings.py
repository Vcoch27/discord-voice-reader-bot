import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True, slots=True)
class Settings:
    discord_token: str = os.getenv("DISCORD_TOKEN", "")
    command_prefix: str = os.getenv("COMMAND_PREFIX", "!")
    ffmpeg_executable: str = os.getenv("FFMPEG_EXECUTABLE", "ffmpeg")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    tts_rate: str = os.getenv("TTS_RATE", "+0%")
    tts_volume: str = os.getenv("TTS_VOLUME", "+0%")
    tts_pitch: str = os.getenv("TTS_PITCH", "+0Hz")


settings = Settings()
