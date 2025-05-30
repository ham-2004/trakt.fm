import discord
from discord.ext import commands
import json
import os
import requests

from database.database import save_history_to_db
from trakt_api import get_full_history

USER_DATA_FILE = "users.json"
TRAKT_API_KEY = os.getenv("TRAKT_API_KEY")

def load_users():
    if not os.path.exists(USER_DATA_FILE):
        return {}
    with open(USER_DATA_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USER_DATA_FILE, "w") as f:
        json.dump(users, f, indent=2)

def trakt_user_exists(username):
    url = f"https://api.trakt.tv/users/{username}"
    headers = {
        "Content-Type": "application/json",
        "trakt-api-version": "2",
        "trakt-api-key": TRAKT_API_KEY
    }
    response = requests.get(url, headers=headers)
    return response.status_code == 200

class RegisterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="tset")
    async def trakt_register(self, ctx, username):
        # Validate the Trakt username first
        if not trakt_user_exists(username):
            embed = discord.Embed(
                title="❌ Invalid Trakt Username",
                description=f"The username `{username}` does not exist on [Trakt](https://trakt.tv). Please double-check and try again.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Save user if valid
        users = load_users()
        users[str(ctx.author.id)] = username
        save_users(users)

        await ctx.send(f"🔄 Fetching full history for `{username}`...")

        shows = get_full_history(username, "shows")
        movies = get_full_history(username, "movies")
        save_history_to_db(username, shows, movies)

        await ctx.send(f"✅ History saved for `{username}`!")

        embed = discord.Embed(
            title="✅ Trakt Account Linked",
            description=f"[**{username}**](https://trakt.tv/users/{username}) has been linked to {ctx.author.mention}",
            color=0x1DB954
        )
        await ctx.send(embed=embed)

# IMPORTANT: async setup function with awaited add_cog
async def setup(bot):
    await bot.add_cog(RegisterCog(bot))


