import asyncio
import logging
from pathlib import Path
import sys

import discord
from discord.ext import commands
import edge_tts

from commands.utility import UtilityCommands
from commands.voice import VoiceCommands
from config.settings import settings, validate_settings
from services.audio_service import AudioService
from services.queue_service import GuildQueueManager
from services.tts_service import EdgeTTSService, VOICE_BY_GENDER, VoiceGender


logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


class VietnameseTTSBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.guilds = True
        intents.voice_states = True

        super().__init__(
            command_prefix=settings.command_prefix,
            intents=intents,
            help_command=None,
        )

        tts_service = EdgeTTSService()
        audio_service = AudioService()
        self.queue_manager = GuildQueueManager(
            tts_service=tts_service,
            audio_service=audio_service,
        )

    async def setup_hook(self) -> None:
        logger.info("Running bot from %s.", Path(__file__).resolve())
        logger.info("Running Python interpreter: %s.", sys.executable)
        logger.info("edge-tts version: %s.", edge_tts.__version__)
        logger.info("Default female voice is %s.", VOICE_BY_GENDER[VoiceGender.FEMALE])

        await self.add_cog(VoiceCommands(self, self.queue_manager))
        await self.add_cog(UtilityCommands(self))

        synced_commands = await self.tree.sync()
        logger.info("Synced %s slash command(s).", len(synced_commands))

    async def on_ready(self) -> None:
        if self.user is None:
            logger.warning("Bot connected, but bot user is unavailable.")
            return

        logger.info("Logged in as %s (%s).", self.user, self.user.id)

    async def close(self) -> None:
        logger.info("Cleaning up guild queues before shutdown.")
        await self.queue_manager.cleanup()
        await super().close()


async def async_main() -> None:
    validate_settings()

    bot = VietnameseTTSBot()
    async with bot:
        await bot.start(settings.discord_token)


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
