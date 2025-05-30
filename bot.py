import os
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from dotenv import load_dotenv
from database.database import init_db

load_dotenv()
init_db()


TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = os.getenv("BOT_PREFIX", "!")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f"✅ Bot is online: {bot.user.name}")

initial_extensions = [
    "models.register",
    "models.recent",
    "models.help",
    "models.recent6",
    "models.watchlist",
]

async def main():
    async with bot:
        for ext in initial_extensions:
            await bot.load_extension(ext)
        await bot.start(TOKEN)

asyncio.run(main())



