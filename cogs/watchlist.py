import discord
from discord.ext import commands
import math

from config import FALLBACK_POSTER
from utils.embeds import error_embed, loading_embed
from database.database import get_user
from api.trakt_api import get_trakt_watchlist
from api.tmbd_api import get_tmdb_movie_poster, get_tmdb_show_poster
from discord import app_commands


class WatchlistView(discord.ui.View):
    def __init__(self, ctx, watchlist, username):
        super().__init__(timeout=120)  # Buttons expire after 2 mins
        self.ctx = ctx
        self.watchlist = watchlist
        self.username = username
        self.view_mode = "list"  # Starts in list mode
        self.current_page = 0

    @property
    def items_per_page(self):
        return 5 if self.view_mode == "list" else 1

    @property
    def max_pages(self):
        return math.ceil(len(self.watchlist) / self.items_per_page) - 1

    async def generate_embed(self):
        start = self.current_page * self.items_per_page
        end = start + self.items_per_page
        current_items = self.watchlist[start:end]

        if self.view_mode == "list":
            # --- LIST VIEW (No photos, no type text) ---
            embed = discord.Embed(
                title=f"📝 {self.ctx.author.display_name}'s Watchlist",
                url=f"https://trakt.tv/users/{self.username}/watchlist",
                color=0x1DB954
            )

            for entry in current_items:
                item_type = entry.get('type')
                item = entry.get(item_type, {})
                title = item.get('title', 'Unknown')
                year = item.get('year', 'Unknown')

                icon = "🎬" if item_type == 'movie' else "📺"
                # Used an invisible character ("\u200b") to remove the "Type: Movie" text!
                embed.add_field(name=f"{icon} {title} ({year})", value="\u200b", inline=False)

            embed.set_footer(
                text=f"Page {self.current_page + 1} of {self.max_pages + 1} | Total Items: {len(self.watchlist)}")
            return embed

        else:
            # --- SINGLE ITEM VIEW (Big photo, no type text) ---
            entry = current_items[0]
            item_type = entry.get('type')
            item = entry.get(item_type, {})
            title = item.get('title', 'Unknown')
            year = item.get('year', 'Unknown')
            icon = "🎬" if item_type == 'movie' else "📺"

            embed = discord.Embed(
                title=f"{icon} {title} ({year})",
                url=f"https://trakt.tv/users/{self.username}/watchlist",
                # Removed the description line here completely!
                color=0x1DB954
            )

            poster_url = None
            if item_type == 'movie':
                poster_url = await get_tmdb_movie_poster(title, year)
            elif item_type == 'show':
                poster_url = await get_tmdb_show_poster(title, year)

            embed.set_image(url=poster_url if poster_url else FALLBACK_POSTER)
            embed.set_footer(text=f"Item {self.current_page + 1} of {len(self.watchlist)}")
            return embed

    @discord.ui.button(label="⬅️ Previous", style=discord.ButtonStyle.secondary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("This isn't your watchlist!", ephemeral=True)

        if self.current_page > 0:
            self.current_page -= 1
            embed = await self.generate_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="Next ➡️", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("This isn't your watchlist!", ephemeral=True)

        if self.current_page < self.max_pages:
            self.current_page += 1
            embed = await self.generate_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="🔀 Toggle View", style=discord.ButtonStyle.success)
    async def toggle_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("This isn't your watchlist!", ephemeral=True)

        self.view_mode = "single" if self.view_mode == "list" else "list"
        self.current_page = 0

        embed = await self.generate_embed()
        await interaction.response.edit_message(embed=embed, view=self)


class WatchlistCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="tw", description="Show your interactive Trakt watchlist")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def trakt_watchlist(self, ctx):
        username = get_user(ctx.author.id)
        if not username:
            return await ctx.send(embed=error_embed("You haven't linked your Trakt account. Use `/tset <username>`"))

        loading_msg = await ctx.send(embed=loading_embed("Fetching your watchlist..."))
        watchlist = await get_trakt_watchlist(username)

        if not watchlist:
            return await loading_msg.edit(embed=error_embed("Your watchlist is empty!"))

        view = WatchlistView(ctx, watchlist, username)
        first_page_embed = await view.generate_embed()

        await loading_msg.delete()
        await ctx.send(embed=first_page_embed, view=view)


async def setup(bot):
    await bot.add_cog(WatchlistCog(bot))