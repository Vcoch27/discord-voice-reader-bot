import asyncio
import logging
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
        self.temp_dir = settings.audio_temp_dir
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        if settings.cleanup_temp_on_start:
            self.cleanup_stale_temp_files()

    def cleanup_stale_temp_files(self) -> None:
        deleted_count = 0
        for file_path in self.temp_dir.glob("tts-*.mp3"):
            try:
                file_path.unlink(missing_ok=True)
                deleted_count += 1
            except OSError:
                logger.warning("Failed to delete stale temporary audio file: %s", file_path)

        if deleted_count:
            logger.info("Deleted %s stale temporary audio file(s).", deleted_count)

    async def synthesize(self, text: str, gender: VoiceGender) -> Path:
        if len(text) > settings.max_tts_chars:
            raise ValueError(f"TTS text must be {settings.max_tts_chars} characters or fewer.")

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
                "Starting TTS generation: voice=%s gender=%s chars=%s timeout=%ss.",
                voice_name,
                gender,
                len(text),
                settings.tts_timeout_seconds,
            )

            await asyncio.wait_for(
                communicate.save(str(file_path)),
                timeout=settings.tts_timeout_seconds,
            )
            logger.info("Successfully saved TTS audio to %s", file_path)
            return file_path
        except asyncio.TimeoutError:
            await self.delete_temp_file(file_path)
            logger.error("TTS generation timed out after %s seconds.", settings.tts_timeout_seconds)
            raise
        except Exception as e:
            await self.delete_temp_file(file_path)
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
