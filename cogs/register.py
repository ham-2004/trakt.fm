import discord
from discord.ext import commands
import aiohttp  # Upgraded from 'requests'

# Centralized imports
from config import TRAKT_API_KEY
from database.database import save_history_to_db, save_user
from api.trakt_api import get_full_history
from utils.embeds import error_embed, success_embed, loading_embed


# Upgraded to async so it doesn't freeze your bot!
async def trakt_user_exists(username):
    url = f"https://api.trakt.tv/users/{username}"
    headers = {
        "Content-Type": "application/json",
        "trakt-api-version": "2",
        "trakt-api-key": TRAKT_API_KEY
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as response:
                return response.status == 200
        except Exception:
            return False


class RegisterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Converted to Hybrid Command
    @commands.hybrid_command(name="tset", description="Link your Trakt.tv account to the bot")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def trakt_register(self, ctx, username: str):
        # We must 'await' the newly async check
        if not await trakt_user_exists(username):
            await ctx.send(embed=error_embed(
                title="Invalid Trakt Username",
                description=f"The username `{username}` does not exist on [Trakt](https://trakt.tv)."
            ))
            return

        # Save to SQLite
        save_user(ctx.author.id, username)

        # Send loading message
        loading_msg = await ctx.send(embed=loading_embed(
            f"Fetching full history for `{username}`...\n*(This may take a minute for large accounts)*"))

        # Fetch history
        shows = await get_full_history(username, "shows")
        movies = await get_full_history(username, "movies")

        # Save history to SQLite
        save_history_to_db(username, shows, movies)

        # Edit the loading message into the ONLY success message
        await loading_msg.edit(embed=success_embed(
            title="Trakt Account Linked",
            description=f"[**{username}**](https://trakt.tv/users/{username}) has been linked to {ctx.author.mention} and history is saved!"
        ))


async def setup(bot):
    await bot.add_cog(RegisterCog(bot))