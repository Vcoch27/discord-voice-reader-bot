import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path

import discord

from services.audio_service import AudioService
from services.tts_service import EdgeTTSService, VOICE_BY_GENDER, VoiceGender

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class TTSQueueItem:
    voice_client: discord.VoiceClient
    text: str
    gender: VoiceGender


class GuildTTSQueue:
    def __init__(
        self,
        guild_id: int,
        tts_service: EdgeTTSService,
        audio_service: AudioService,
    ) -> None:
        self.guild_id = guild_id
        self.tts_service = tts_service
        self.audio_service = audio_service
        self.queue: asyncio.Queue[TTSQueueItem] = asyncio.Queue()
        self.worker_task: asyncio.Task[None] | None = None
        self.stop_event = asyncio.Event()
        self.is_playing = False
        self.voice_gender = VoiceGender.FEMALE

    async def enqueue(self, voice_client: discord.VoiceClient, text: str) -> int:
        item = TTSQueueItem(
            voice_client=voice_client,
            text=text,
            gender=self.voice_gender,
        )
        await self.queue.put(item)
        position = self.queue.qsize() + (1 if self.is_playing else 0)

        if self.worker_task is None or self.worker_task.done():
            self.stop_event.clear()
            self.worker_task = asyncio.create_task(
                self._worker(),
                name=f"tts-worker-{self.guild_id}",
            )

        return position

    def current_voice_name(self) -> str:
        return VOICE_BY_GENDER[self.voice_gender]

    def set_voice_gender(self, gender: VoiceGender) -> str:
        old_gender = self.voice_gender
        self.voice_gender = gender
        voice_name = VOICE_BY_GENDER[gender]
        logger.info(
            "Guild %s: Voice gender changed from %s to %s. Using voice: %s",
            self.guild_id,
            old_gender,
            gender,
            voice_name,
        )
        return voice_name

    async def stop(self) -> None:
        self.stop_event.set()
        self._clear_queue()

        if self.worker_task is not None and not self.worker_task.done():
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass

        self.worker_task = None

    async def _worker(self) -> None:
        logger.info("Started TTS worker for guild %s.", self.guild_id)

        try:
            while not self.stop_event.is_set():
                try:
                    # Use wait_for with timeout to avoid infinite waiting
                    item = await asyncio.wait_for(
                        self.queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    if self.queue.empty():
                        break
                    continue
                
                temp_file: Path | None = None

                try:
                    self.is_playing = True
                    if item.voice_client.is_playing() or item.voice_client.is_paused():
                        item.voice_client.stop()

                    temp_file = await self.tts_service.synthesize(
                        text=item.text,
                        gender=item.gender,
                    )
                    await self.audio_service.play(item.voice_client, temp_file)
                    logger.debug("Successfully played TTS for guild %s with voice gender %s.", self.guild_id, item.gender)
                except asyncio.CancelledError:
                    if item.voice_client.is_playing() or item.voice_client.is_paused():
                        item.voice_client.stop()
                    raise
                except Exception:
                    logger.exception("Failed to process TTS queue item for guild %s.", self.guild_id)
                finally:
                    self.is_playing = False
                    if temp_file is not None:
                        # await self.tts_service.delete_temp_file(temp_file)
                        print("TEMP FILE KEPT =", temp_file)
                    self.queue.task_done()
        finally:
            logger.info("Stopped TTS worker for guild %s.", self.guild_id)

    def _clear_queue(self) -> None:
        while True:
            try:
                self.queue.get_nowait()
                self.queue.task_done()
            except asyncio.QueueEmpty:
                break


class GuildQueueManager:
    def __init__(
        self,
        tts_service: EdgeTTSService,
        audio_service: AudioService,
    ) -> None:
        self.tts_service = tts_service
        self.audio_service = audio_service
        self.guild_queues: dict[int, GuildTTSQueue] = {}

    async def enqueue(
        self,
        guild_id: int,
        voice_client: discord.VoiceClient,
        text: str,
    ) -> int:
        guild_queue = self._get_or_create_queue(guild_id)
        return await guild_queue.enqueue(voice_client=voice_client, text=text)

    def current_voice_name(self, guild_id: int) -> str:
        guild_queue = self._get_or_create_queue(guild_id)
        return guild_queue.current_voice_name()

    def set_voice_gender(self, guild_id: int, gender: VoiceGender) -> str:
        guild_queue = self._get_or_create_queue(guild_id)
        return guild_queue.set_voice_gender(gender)

    async def stop(self, guild_id: int) -> None:
        guild_queue = self.guild_queues.get(guild_id)
        if guild_queue is None:
            return

        await guild_queue.stop()

    async def cleanup(self) -> None:
        await asyncio.gather(
            *(guild_queue.stop() for guild_queue in self.guild_queues.values()),
            return_exceptions=True,
        )

    def _get_or_create_queue(self, guild_id: int) -> GuildTTSQueue:
        guild_queue = self.guild_queues.get(guild_id)
        if guild_queue is None:
            guild_queue = GuildTTSQueue(guild_id, self.tts_service, self.audio_service)
            self.guild_queues[guild_id] = guild_queue

        return guild_queue
