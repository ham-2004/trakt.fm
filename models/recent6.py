import requests
import discord
from discord.ext import commands
import os
import json
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import aiohttp

from tmbd_api import get_tmdb_movie_poster
from trakt_api import get_recent_activity, get_full_history

USER_DATA_FILE = "users.json"
TRAKT_API_KEY = os.getenv("TRAKT_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
FALLBACK_POSTER = "https://i.imgur.com/Z2MYNbj.png"
IMAGE_CACHE_DIR = "image_cache"


def load_users():
    if not os.path.exists(USER_DATA_FILE):
        return {}
    with open(USER_DATA_FILE, "r") as f:
        return json.load(f)


class Recent6Cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="t6")
    async def trakt_six_recent(self, ctx):
        """Show 6 recent movies in a grid image with overlaid titles"""
        users = load_users()
        user_id = str(ctx.author.id)

        if user_id not in users:
            await ctx.send("❌ Please register first using `trakt_register <username>`")
            return

        username = users[user_id]
        history = get_full_history(username)

        if not history:
            await ctx.send("❌ No recent activity found.")
            return

        # Gather up to 6 recent movies
        movies = [entry for entry in history if 'movie' in entry][:6]

        if not movies:
            await ctx.send("❌ No recent movies found.")
            return

        # Prepare poster URLs and titles
        grid_data = []
        for entry in movies:
            item = entry["movie"]
            title = item.get("title", "Unknown")
            year = item.get("year", "Unknown")
            full_title = f"{title} ({year})"
            poster_url = item.get("images", {}).get("poster", [None])[0]

            if not poster_url:
                poster_url = get_tmdb_movie_poster(title, year)

            if not poster_url:
                poster_url = FALLBACK_POSTER
            elif not poster_url.startswith("http"):
                poster_url = "https://" + poster_url

            grid_data.append((poster_url, full_title))

        # Create grid image
        image_bytes = await self.create_titled_image_grid(grid_data)

        if not image_bytes:
            await ctx.send("❌ Failed to generate grid image.")
            return

        # Count total scrobbles
        total_scrobbles = len(history)

        embed = discord.Embed(
            title=f"🎬 Recent Movies for {ctx.author.display_name}",
            color=0x2F3136,
            url=f"https://trakt.tv/users/{username}"
        )
        embed.set_image(url="attachment://grid.webp")
        embed.set_footer(text=f"📊 Total scrobbles: {total_scrobbles}")

        file = discord.File(image_bytes, filename="grid.webp")
        await ctx.send(embed=embed, file=file)

    async def create_titled_image_grid(self, image_data):
        from PIL import Image, ImageDraw, ImageFont
        import aiohttp

        POSTER_WIDTH = 200
        POSTER_HEIGHT = 300
        GRID_COLS = 3
        GRID_ROWS = 2

        grid = Image.new('RGB', (POSTER_WIDTH * GRID_COLS, POSTER_HEIGHT * GRID_ROWS), (0, 0, 0))

        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except:
            font = ImageFont.load_default()

        async with aiohttp.ClientSession() as session:
            for index, (url, title) in enumerate(image_data):
                try:
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            img_data = await resp.read()
                            img = Image.open(BytesIO(img_data)).convert("RGB")
                        else:
                            continue
                except Exception:
                    continue

                img = img.resize((POSTER_WIDTH, POSTER_HEIGHT))
                draw = ImageDraw.Draw(img)

                # Background for text
                draw.rectangle(
                    [(0, POSTER_HEIGHT - 30), (POSTER_WIDTH, POSTER_HEIGHT)],
                    fill=(0, 0, 0, 128)
                )

                draw.text(
                    (10, POSTER_HEIGHT - 25),
                    title,
                    font=font,
                    fill=(255, 255, 255),
                    stroke_width=1,
                    stroke_fill=(0, 0, 0)
                )

                x = (index % GRID_COLS) * POSTER_WIDTH
                y = (index // GRID_COLS) * POSTER_HEIGHT
                grid.paste(img, (x, y))

        # Save grid to memory
        buffer = BytesIO()
        grid.save(buffer, format="WEBP")
        buffer.seek(0)
        return buffer

async def setup(bot):
    await bot.add_cog(Recent6Cog(bot))