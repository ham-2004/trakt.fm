import discord
from discord.ext import commands
import requests
import os
import json
from PIL import Image
from io import BytesIO


USER_DATA_FILE = "users.json"
TRAKT_API_KEY = os.getenv("TRAKT_API_KEY")
FALLBACK_POSTER = "https://i.imgur.com/Z2MYNbj.png"
IMAGE_CACHE_DIR = "image_cache"

def load_users():
    if not os.path.exists(USER_DATA_FILE):
        return {}
    with open(USER_DATA_FILE, "r") as f:
        return json.load(f)


class WatchlistCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="tw")
    async def trakt_watchlist(self, ctx):
        users = load_users()
        user_id = str(ctx.author.id)
        if user_id not in users:
            await ctx.send("❌ Please register first using `trakt_register <username>`")
            return

        username = users[user_id]

        headers = {
            "Content-Type": "application/json",
            "trakt-api-version": "2",
            "trakt-api-key": "TRAKT_CLIENT_ID"
        }

        url = f"https://api.trakt.tv/users/{username}/watchlist"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            await ctx.send("❌ Failed to fetch watchlist.")
            return

        watchlist = response.json()[:6]
        if not watchlist:
            await ctx.send("📭 Your watchlist is empty.")
            return

        posters = []
        titles = []

        for entry in watchlist:
            media_type = entry.get("type")
            item = entry.get(media_type, {})
            title = item.get("title", "Unknown")
            year = item.get("year", "Unknown")
            slug = item.get("ids", {}).get("slug", "")
            trakt_url = f"https://trakt.tv/{media_type}s/{slug}"
            titles.append(f"[{title} ({year})]({trakt_url})")

            # Fetch poster
            poster = item.get('images', {}).get('poster', [None])[0]
            if poster:
                poster_url = "https://" + poster
                try:
                    img_response = requests.get(poster_url)
                    img = Image.open(BytesIO(img_response.content)).resize((300, 450))
                    posters.append(img)
                except:
                    continue

        if not posters:
            await ctx.send("❌ Could not load any posters.")
            return

        # Create 3x2 grid image
        grid_width = 3
        grid_height = 2
        poster_width, poster_height = 300, 450
        grid_image = Image.new("RGB", (grid_width * poster_width, grid_height * poster_height))

        for idx, poster in enumerate(posters):
            x = (idx % grid_width) * poster_width
            y = (idx // grid_width) * poster_height
            grid_image.paste(poster, (x, y))

        grid_path = f"watchlist_{user_id}.jpg"
        grid_image.save(grid_path)

        # Create embed
        embed = discord.Embed(
            title=f"🎬 {ctx.author.display_name}'s Trakt Watchlist (Top 6)",
            url=f"https://trakt.tv/users/{username}/watchlist",
            color=0xe74c3c
        )
        embed.description = "\n".join(f"• {t}" for t in titles)

        file = discord.File(grid_path, filename="watchlist.jpg")
        embed.set_image(url="attachment://watchlist.jpg")

        await ctx.send(embed=embed, file=file)

        os.remove(grid_path)  # Clean up


async def setup(bot):
    await bot.add_cog(WatchlistCog(bot))
