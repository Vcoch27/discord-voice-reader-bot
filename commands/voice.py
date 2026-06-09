import logging

import discord
from discord import app_commands
from discord.ext import commands

from config.settings import settings
from services.queue_service import GuildQueueManager
from services.tts_service import VoiceGender

logger = logging.getLogger(__name__)


class VoiceCommands(commands.Cog):
    def __init__(self, bot: commands.Bot, queue_manager: GuildQueueManager) -> None:
        self.bot = bot
        self.queue_manager = queue_manager

    @app_commands.command(name="tts", description="Read Vietnamese text aloud in your voice channel.")
    @app_commands.describe(text="Vietnamese text to read aloud.")
    async def tts(
        self,
        interaction: discord.Interaction,
        text: app_commands.Range[str, 1, 1000],
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        try:
            voice_channel = self._get_user_voice_channel(interaction)
            voice_client = await self._connect_or_move(interaction, voice_channel)
            position = await self.queue_manager.enqueue(
                guild_id=interaction.guild.id,
                voice_client=voice_client,
                text=str(text),
                user_id=interaction.user.id,
                user_display_name=interaction.user.display_name,
            )
            voice_name = self.queue_manager.current_voice_name(interaction.guild.id)
            logger.info(
                "Accepted /tts request guild_id=%s user_id=%s chars=%s.",
                interaction.guild.id,
                interaction.user.id,
                len(str(text)),
            )
        except ValueError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return
        except discord.DiscordException:
            logger.exception("Discord voice operation failed.")
            await interaction.response.send_message(
                "I could not join or play audio in your voice channel.",
                ephemeral=True,
            )
            return
        except Exception:
            logger.exception("Failed to enqueue TTS request.")
            await interaction.response.send_message(
                "Something went wrong while preparing TTS.",
                ephemeral=True,
            )
            return

        if position == 1:
            message = f"Reading your message now.\nVoice: {voice_name}"
        else:
            message = (
                f"Queued your message at position {position}.\n"
                f"Voice: {voice_name}\nQueue limit: {settings.max_queue_size}"
            )

        await interaction.response.send_message(message, ephemeral=True)

    @app_commands.command(name="voice", description="Choose the Vietnamese TTS voice.")
    @app_commands.describe(gender="Voice gender to use for this server.")
    @app_commands.choices(
        gender=[
            app_commands.Choice(name="female", value="female"),
            app_commands.Choice(name="male", value="male"),
        ],
    )
    async def voice(
        self,
        interaction: discord.Interaction,
        gender: app_commands.Choice[str],
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        selected_gender = VoiceGender(gender.value)
        voice_name = self.queue_manager.set_voice_gender(
            guild_id=interaction.guild.id,
            gender=selected_gender,
        )

        await interaction.response.send_message(
            f"Voice changed successfully.\nGender: {gender.value}\nVoice: {voice_name}",
            ephemeral=True,
        )

    @app_commands.command(name="join", description="Join your current voice channel.")
    async def join(self, interaction: discord.Interaction) -> None:
        try:
            voice_channel = self._get_user_voice_channel(interaction)
            voice_client = await self._connect_or_move(interaction, voice_channel)
        except ValueError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return
        except discord.DiscordException:
            logger.exception("Failed to join voice channel.")
            await interaction.response.send_message(
                "I could not join your voice channel.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"Joined {voice_client.channel.mention}.",
            ephemeral=True,
        )

    @app_commands.command(name="leave", description="Disconnect from the voice channel.")
    async def leave(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        await self.queue_manager.stop(interaction.guild.id)

        voice_client = interaction.guild.voice_client
        if voice_client is None:
            await interaction.response.send_message(
                "I am not connected to a voice channel.",
                ephemeral=True,
            )
            return

        await voice_client.disconnect(force=True)
        await interaction.response.send_message("Disconnected.", ephemeral=True)

    @app_commands.command(name="stop", description="Stop current playback and clear the queue.")
    async def stop(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        await self.queue_manager.stop(interaction.guild.id)
        await interaction.response.send_message(
            "Stopped playback and cleared the queue.",
            ephemeral=True,
        )

    def _get_user_voice_channel(
        self,
        interaction: discord.Interaction,
    ) -> discord.VoiceChannel | discord.StageChannel:
        if interaction.guild is None:
            raise ValueError("This command can only be used in a server.")

        user = interaction.user
        if not isinstance(user, discord.Member) or user.voice is None or user.voice.channel is None:
            raise ValueError("Join a voice channel first.")

        return user.voice.channel

    async def _connect_or_move(
        self,
        interaction: discord.Interaction,
        voice_channel: discord.VoiceChannel | discord.StageChannel,
    ) -> discord.VoiceClient:
        if interaction.guild is None:
            raise ValueError("This command can only be used in a server.")

        voice_client = interaction.guild.voice_client
        if voice_client is None:
            connected_client = await voice_channel.connect(self_deaf=True)
            return connected_client

        if voice_client.channel != voice_channel:
            await voice_client.move_to(voice_channel)

        return voice_client
