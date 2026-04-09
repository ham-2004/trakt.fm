import discord
import random
from discord.ext import commands
from discord import app_commands
from typing import Union
from datetime import datetime, timezone

from config import FALLBACK_POSTER
from utils.embeds import error_embed, success_embed, loading_embed
from database.database import get_user, delete_user
from api.trakt_api import get_trakt_watchlist, get_user_stats, get_trending_trakt
from api.tmbd_api import get_tmdb_movie_poster, get_tmdb_show_poster


class DiscoveryCog(commands.Cog):
    """Discovery & social commands – random picks, comparisons, trending, and account management."""

    def __init__(self, bot):
        self.bot = bot

    # ------------------------------------------------------------------ #
    # /random – Pick a random item from the user's Trakt watchlist
    # ------------------------------------------------------------------ #
    @commands.hybrid_command(
        name="random",
        description="Pick a random movie or show from your Trakt watchlist"
    )
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def random_pick(self, ctx):
        # Step 1 – Resolve user
        username = get_user(ctx.author.id)
        if not username:
            return await ctx.send(
                embed=error_embed("You haven't linked your Trakt account. Use `/tset <username>`")
            )

        # Step 2 – Show a loading state while we fetch data
        loading_msg = await ctx.send(embed=loading_embed("Rolling the dice on your watchlist… 🎲"))

        try:
            watchlist = await get_trakt_watchlist(username)

            if not watchlist:
                return await loading_msg.edit(
                    embed=error_embed("Your watchlist is empty! Add some titles on Trakt first.")
                )

            # Step 3 – Pick a random entry
            pick = random.choice(watchlist)
            item_type = pick.get("type")  # 'movie' or 'show'
            item = pick.get(item_type, {})
            title = item.get("title", "Unknown")
            year = item.get("year", "Unknown")

            # Step 4 – Fetch the poster from TMDB
            if item_type == "movie":
                poster_url = await get_tmdb_movie_poster(title, year)
            else:
                poster_url = await get_tmdb_show_poster(title, year)

            icon = "🎬" if item_type == "movie" else "📺"
            kind = "Movie" if item_type == "movie" else "Show"

            # Step 5 – Build a beautiful suggestion embed
            embed = discord.Embed(
                title=f"{icon} {title} ({year})",
                description=(
                    f"**Tonight's pick from your watchlist!**\n\n"
                    f"*We randomly selected this {kind.lower()} for you.*\n"
                    f"Grab the popcorn and enjoy!"
                ),
                color=0xE4A010,  # Warm gold
                url=f"https://trakt.tv/users/{username}/watchlist"
            )
            embed.set_author(
                name=f"🎰 Random Pick • {ctx.author.display_name}",
                icon_url=ctx.author.display_avatar.url
            )
            embed.set_image(url=poster_url if poster_url else FALLBACK_POSTER)
            embed.set_footer(text=f"From your Trakt watchlist ({len(watchlist)} items)")
            embed.timestamp = datetime.now(timezone.utc)

            await loading_msg.edit(embed=embed)

        except Exception as e:
            print(f"❌ CRASH in /random: {e}")
            await loading_msg.edit(embed=error_embed("Something went wrong fetching your watchlist."))

    # ------------------------------------------------------------------ #
    # /compare – Side-by-side stats comparison with another user
    # ------------------------------------------------------------------ #
    @commands.hybrid_command(
        name="compare",
        description="Compare your Trakt stats with another user"
    )
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def compare(self, ctx, target: Union[discord.Member, discord.User]):
        # Step 1 – Resolve both users
        author_username = get_user(ctx.author.id)
        target_username = get_user(target.id)

        if not author_username:
            return await ctx.send(
                embed=error_embed("You haven't linked your Trakt account. Use `/tset <username>`")
            )
        if not target_username:
            return await ctx.send(
                embed=error_embed(f"{target.display_name} hasn't linked their Trakt account yet.")
            )

        # Step 2 – Loading state
        loading_msg = await ctx.send(embed=loading_embed("Crunching the numbers… 📊"))

        try:
            # Step 3 – Fetch stats for both users in parallel-ish fashion
            author_stats = await get_user_stats(author_username)
            target_stats = await get_user_stats(target_username)

            if not author_stats or not target_stats:
                return await loading_msg.edit(
                    embed=error_embed("Could not fetch stats for one or both users. Try again later.")
                )

            # --- Helper to extract readable numbers ---
            def extract(stats):
                movies_plays = stats.get("movies", {}).get("watched", 0)
                shows_plays = stats.get("shows", {}).get("watched", 0)
                episodes_plays = stats.get("episodes", {}).get("watched", 0)
                movies_mins = stats.get("movies", {}).get("minutes", 0)
                shows_mins = stats.get("episodes", {}).get("minutes", 0)
                total_days = round((movies_mins + shows_mins) / 1440, 1)
                return movies_plays, shows_plays, episodes_plays, total_days

            a_movies, a_shows, a_eps, a_days = extract(author_stats)
            t_movies, t_shows, t_eps, t_days = extract(target_stats)

            # Step 4 – Build comparison embed
            embed = discord.Embed(
                title="⚔️ Stats Showdown",
                description=f"**{ctx.author.display_name}** vs **{target.display_name}**\n━━━━━━━━━━━━━━━━━━━━",
                color=0x9B59B6  # Purple for rivalry
            )

            # Author column
            embed.add_field(
                name=f"🎬 {ctx.author.display_name}",
                value=(
                    f"**Movies:** {a_movies:,}\n"
                    f"**Shows:** {a_shows:,}\n"
                    f"**Episodes:** {a_eps:,}\n"
                    f"**Watch Time:** {a_days:,} days"
                ),
                inline=True
            )

            # VS column
            embed.add_field(
                name="⚡",
                value="vs\nvs\nvs\nvs",
                inline=True
            )

            # Target column
            embed.add_field(
                name=f"🎬 {target.display_name}",
                value=(
                    f"**Movies:** {t_movies:,}\n"
                    f"**Shows:** {t_shows:,}\n"
                    f"**Episodes:** {t_eps:,}\n"
                    f"**Watch Time:** {t_days:,} days"
                ),
                inline=True
            )

            # Winner callout
            if a_days > t_days:
                verdict = f"👑 **{ctx.author.display_name}** leads with **{a_days - t_days:.1f}** more days watched!"
            elif t_days > a_days:
                verdict = f"👑 **{target.display_name}** leads with **{t_days - a_days:.1f}** more days watched!"
            else:
                verdict = "🤝 It's a perfect tie! You're both equally addicted."

            embed.add_field(name="━━━━━━━━━━━━━━━━━━━━", value=verdict, inline=False)

            embed.set_footer(text="Stats powered by Trakt.tv")
            embed.timestamp = datetime.now(timezone.utc)

            await loading_msg.edit(embed=embed)

        except Exception as e:
            print(f"❌ CRASH in /compare: {e}")
            await loading_msg.edit(embed=error_embed("Failed to compare stats. Check console."))

    # ------------------------------------------------------------------ #
    # /trending – Show the top 5 trending movies/shows on Trakt right now
    # ------------------------------------------------------------------ #
    @commands.hybrid_command(
        name="trending",
        description="See what's trending on Trakt right now"
    )
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def trending(self, ctx):
        loading_msg = await ctx.send(embed=loading_embed("Fetching what's trending worldwide… 🌍"))

        try:
            trending_items = await get_trending_trakt()

            if not trending_items:
                return await loading_msg.edit(
                    embed=error_embed("Could not fetch trending data right now. Try again later.")
                )

            embed = discord.Embed(
                title="🔥 Trending on Trakt",
                description="The hottest movies & shows people are watching right now.\n━━━━━━━━━━━━━━━━━━━━",
                color=0xED1C24  # Trakt red
            )

            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]

            for index, item in enumerate(trending_items[:5]):
                # Trending endpoint may return 'movie' or 'show' as the type
                watchers = item.get("watchers", 0)

                if "movie" in item:
                    media = item["movie"]
                    kind = "🎬"
                elif "show" in item:
                    media = item["show"]
                    kind = "📺"
                else:
                    continue

                title = media.get("title", "Unknown")
                year = media.get("year", "?")

                embed.add_field(
                    name=f"{medals[index]} {kind} {title} ({year})",
                    value=f"👀 **{watchers:,}** people watching now",
                    inline=False
                )

            embed.set_footer(text="Data from Trakt.tv • Updates frequently")
            embed.timestamp = datetime.now(timezone.utc)

            await loading_msg.edit(embed=embed)

        except Exception as e:
            print(f"❌ CRASH in /trending: {e}")
            await loading_msg.edit(embed=error_embed("Failed to load trending data. Check console."))


# ------------------------------------------------------------------ #
# Cog setup hook – called by bot.load_extension("cogs.discovery")
# ------------------------------------------------------------------ #
async def setup(bot):
    await bot.add_cog(DiscoveryCog(bot))
