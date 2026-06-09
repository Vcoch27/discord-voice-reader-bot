import discord
from discord import app_commands
from discord.ext import commands


class UtilityCommands(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="ping", description="Health check.")
    async def ping(self, interaction: discord.Interaction) -> None:
        latency_ms = round(self.bot.latency * 1000)
        await interaction.response.send_message(
            f"Pong! Latency: {latency_ms} ms",
            ephemeral=True,
        )
