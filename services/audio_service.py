import asyncio
import logging
from pathlib import Path

import discord

from config.settings import settings

logger = logging.getLogger(__name__)


class AudioService:
    def create_audio_source(self, file_path: Path) -> discord.AudioSource:
        return discord.FFmpegPCMAudio(
            executable=settings.ffmpeg_executable,
            source=str(file_path),
            before_options="-nostdin -hide_banner -loglevel warning",
            # Removed loudnorm filter to prevent voice distortion
            # Using -filter:a loudnorm=I=-16:TP=-1.5:LRA=11 can cause voice compression
            options="-vn -af \"volume=0.8\" -ar 48000 -ac 2",
        )

    async def play(
        self,
        voice_client: discord.VoiceClient,
        file_path: Path,
    ) -> None:
        if not voice_client.is_connected():
            raise RuntimeError("Voice client is not connected.")

        finished = asyncio.Event()
        loop = asyncio.get_running_loop()
        playback_error: Exception | None = None

        def after(error: Exception | None) -> None:
            nonlocal playback_error
            playback_error = error
            loop.call_soon_threadsafe(finished.set)

        source = self.create_audio_source(file_path)
        voice_client.play(source, after=after)
        await finished.wait()

        if playback_error is not None:
            logger.error("FFmpeg playback failed: %s", playback_error)
            raise playback_error
