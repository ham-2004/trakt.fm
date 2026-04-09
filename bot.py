import os
import sys  # <-- NEW: Import sys
import discord
import math
import logging
from discord.ext import commands
from discord import app_commands
import asyncio
from dotenv import load_dotenv
from database.database import init_db
from utils.embeds import error_embed

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = os.getenv("BOT_PREFIX", "!")

# --- NEW: Force Windows to use UTF-8 for terminal output ---
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# --- UPDATED: Configure basic logging with utf-8 encoding ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),  # <-- NEW: Explicitly set utf-8
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("trakt.fm")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

@bot.event
async def on_ready():
    logger.info(f"✅ Bot is online: {bot.user.name}")
    try:
        synced = await bot.tree.sync()
        logger.info(f"🔄 Synced {len(synced)} slash command(s)")
    except Exception as e:
        logger.error(f"⚠️ Failed to sync commands: {e}")

@bot.event
async def on_command_error(ctx, error):
    """Global error handler for all commands."""

    if isinstance(error, commands.CommandNotFound):
        return

    if isinstance(error, commands.CommandOnCooldown):
        seconds_left = math.ceil(error.retry_after)
        embed = error_embed(
            title="Slow Down!",
            description=f"You are using this command too fast. Please try again in **{seconds_left} seconds**."
        )
        await ctx.send(embed=embed, delete_after=5.0)
        return

    if isinstance(error, commands.MissingRequiredArgument):
        embed = error_embed(
            title="Missing Argument",
            description=f"You are missing a required argument: `{error.param.name}`\n"
                        f"**Usage:** `{ctx.prefix}{ctx.command.name} {ctx.command.signature}`"
        )
        await ctx.send(embed=embed)
        return

    if isinstance(error, commands.CommandInvokeError):
        logger.error(f"⚠️ Error in command {ctx.command}: {error.original}")
        embed = error_embed(
            title="Internal Error",
            description="Something went wrong while processing your request. Please try again later."
        )
        await ctx.send(embed=embed)
        return

    # --- NEW: Safe fallback handler ---
    logger.warning(f"Unhandled error type caught: {error}")
    await ctx.send(embed=error_embed(
        title="Unexpected Error",
        description="An unexpected error occurred. If this persists, please contact an administrator."
    ))

async def main():
    init_db()
    async with bot:
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py') and not filename.startswith('__'):
                extension_name = f"cogs.{filename[:-3]}"
                try:
                    await bot.load_extension(extension_name)
                    logger.info(f"🧩 Loaded extension: {extension_name}")
                except Exception as e:
                    logger.error(f"⚠️ Failed to load extension {extension_name}: {e}")

        await bot.start(TOKEN)

asyncio.run(main())