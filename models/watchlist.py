import discord
from discord.ext import commands
from discord.ui import Button, View
import requests
import os
import json

from trakt_api import get_trakt_watchlist
from tmbd_api import get_tmdb_movie_poster
from utils.image_grid import create_titled_image_grids

USER_DATA_FILE = "users.json"
TRAKT_API_KEY = os.getenv("TRAKT_API_KEY")
FALLBACK_POSTER = "https://i.imgur.com/Z2MYNbj.png"
IMAGE_CACHE_DIR = "image_cache"


def load_users():
    if not os.path.exists(USER_DATA_FILE):
        return {}
    with open(USER_DATA_FILE, "r") as f:
        return json.load(f)


class WatchlistView(View):
    def __init__(self, watchlist, username, author_name):
        super().__init__(timeout=60)
        self.watchlist = watchlist
        self.username = username
        self.author_name = author_name
        self.current_index = 0
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()

        prev_button = Button(emoji="⬅️", style=discord.ButtonStyle.secondary)
        prev_button.callback = self.previous_item
        self.add_item(prev_button)

        next_button = Button(emoji="➡️", style=discord.ButtonStyle.secondary)
        next_button.callback = self.next_item
        self.add_item(next_button)

        # Add a button to show all items
        show_all_button = Button(emoji="📺", style=discord.ButtonStyle.primary, label="Show All")
        show_all_button.callback = self.show_all
        self.add_item(show_all_button)

    async def get_current_embed(self):
        entry = self.watchlist[self.current_index]
        media_type = entry.get("type")
        item = entry.get(media_type, {})
        title = item.get("title", "Unknown")
        year = item.get("year", "Unknown")
        slug = item.get("ids", {}).get("slug", "")
        trakt_url = f"https://trakt.tv/{media_type}s/{slug}"

        # Resolve poster
        poster_url = item.get('images', {}).get('poster', [None])[0]
        if not poster_url:
            poster_url = get_tmdb_movie_poster(title, year)
        if not poster_url:
            poster_url = FALLBACK_POSTER
        elif not poster_url.startswith("http"):
            poster_url = "https://" + poster_url

        embed = discord.Embed(
            title=f"🎬 {title} ({year})",
            url=trakt_url,
            description=f"**{self.author_name}'s Watchlist**\nItem {self.current_index + 1} of {len(self.watchlist)}",
            color=0xe74c3c
        )
        embed.set_image(url=poster_url)
        embed.set_footer(text=f"Media type: {media_type}")

        return embed

    async def previous_item(self, interaction):
        self.current_index = (self.current_index - 1) % len(self.watchlist)
        embed = await self.get_current_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def next_item(self, interaction):
        self.current_index = (self.current_index + 1) % len(self.watchlist)
        embed = await self.get_current_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def show_all(self, interaction):
        grid_data = []
        titles = []

        for entry in self.watchlist:
            media_type = entry.get("type")
            item = entry.get(media_type, {})
            title = item.get("title", "Unknown")
            year = item.get("year", "Unknown")
            slug = item.get("ids", {}).get("slug", "")
            trakt_url = f"https://trakt.tv/{media_type}s/{slug}"
            titles.append(f"[{title} ({year})]({trakt_url})")

            # Resolve poster
            poster_url = item.get('images', {}).get('poster', [None])[0]
            if not poster_url:
                poster_url = get_tmdb_movie_poster(title, year)
            if not poster_url:
                poster_url = FALLBACK_POSTER
            elif not poster_url.startswith("http"):
                poster_url = "https://" + poster_url

            grid_data.append((poster_url, f"{title} ({year})"))

        image_bytes = await create_titled_image_grids(grid_data)

        embed = discord.Embed(
            title=f"📺 {self.author_name}'s Trakt Watchlist",
            url=f"https://trakt.tv/users/{self.username}/watchlist",
            color=0xe74c3c
        )
        file = discord.File(image_bytes, filename="watchlist.webp")
        embed.set_image(url="attachment://watchlist.webp")

        await interaction.response.edit_message(embed=embed, view=None, attachments=[file])


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
        watchlist = get_trakt_watchlist(username)

        if not watchlist:
            await ctx.send("❌ Failed to fetch or empty watchlist.")
            return

        # Limit to 12 items for practicality
        watchlist = watchlist[:12]

        view = WatchlistView(watchlist, username, ctx.author.display_name)
        initial_embed = await view.get_current_embed()

        await ctx.send(embed=initial_embed, view=view)


async def setup(bot):
    await bot.add_cog(WatchlistCog(bot))