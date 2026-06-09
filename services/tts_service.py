import asyncio
import logging
import tempfile
from enum import StrEnum
from pathlib import Path
from uuid import uuid4

import edge_tts

from config.settings import settings

logger = logging.getLogger(__name__)


class VoiceGender(StrEnum):
    FEMALE = "female"
    MALE = "male"


VOICE_BY_GENDER: dict[VoiceGender, str] = {
    VoiceGender.FEMALE: "vi-VN-HoaiMyNeural",
    VoiceGender.MALE: "vi-VN-NamMinhNeural",
}


class EdgeTTSService:
    def __init__(self) -> None:
        self.temp_dir = Path(tempfile.gettempdir()) / "discord-vietnamese-tts-bot"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    async def synthesize(self, text: str, gender: VoiceGender) -> Path:
        voice_name = VOICE_BY_GENDER[gender]
        file_path = self.temp_dir / f"tts-{uuid4().hex}.mp3"

        try:
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice_name,
                rate=settings.tts_rate,
                volume=settings.tts_volume,
                pitch=settings.tts_pitch,
            )

            logger.info(
                "Synthesizing Vietnamese speech with Edge-TTS voice %s (gender=%s). "
                "Rate=%s, Volume=%s, Pitch=%s",
                voice_name,
                gender,
                settings.tts_rate,
                settings.tts_volume,
                settings.tts_pitch,
            )
            
            await communicate.save(str(file_path))
            logger.info("Successfully saved TTS audio to %s", file_path)
            return file_path
        except Exception as e:
            logger.error(
                "Failed to synthesize TTS with voice %s (gender=%s). Error: %s",
                voice_name,
                gender,
                str(e),
                exc_info=True,
            )
            raise

    async def delete_temp_file(self, file_path: Path) -> None:
        try:
            await asyncio.to_thread(file_path.unlink, missing_ok=True)
        except OSError:
            logger.exception("Failed to delete temporary audio file: %s", file_path)
