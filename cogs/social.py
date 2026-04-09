import discord
from discord.ext import commands
from datetime import datetime, timezone
from discord import app_commands
from typing import Union  # <-- Added to allow commands in DMs

from config import FALLBACK_POSTER
from utils.embeds import error_embed
from database.database import get_user, get_leaderboard, count_total_scrobbles
from api.trakt_api import get_now_playing, get_user_stats, get_trakt_profile
from api.tmbd_api import get_tmdb_movie_poster, get_tmdb_show_poster


class SocialCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="np", description="See what you are currently watching")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def now_playing(self, ctx):
        username = get_user(ctx.author.id)

        if not username:
            return await ctx.send(embed=error_embed("You haven't linked your Trakt account. Use `/tset`"))

        playing = await get_now_playing(username)

        if not playing:
            return await ctx.send(
                embed=error_embed("You aren't watching anything right now! (Or your Trakt scrobbler is delayed)."))

        item_type = playing.get('type')  # Trakt returns 'movie' or 'episode'

        embed = discord.Embed(color=0xED1C24)
        embed.set_author(
            name=f"Now Playing • {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url,
            url=f"https://trakt.tv/users/{username}"
        )

        poster_url = None
        description_lines = []

        # --- THE FIX: Handle Movies and Episodes differently ---
        if item_type == 'movie':
            movie = playing.get('movie', {})
            title = movie.get('title', 'Unknown Movie')
            year = movie.get('year', 'Unknown')

            embed.title = f"🎬 {title} ({year})"
            poster_url = await get_tmdb_movie_poster(title, year)

        elif item_type == 'episode':
            show = playing.get('show', {})
            episode = playing.get('episode', {})

            # Grab the SHOW title for TMDB, not the episode title!
            show_title = show.get('title', 'Unknown Show')
            show_year = show.get('year', 'Unknown')

            season = episode.get('season', 0)
            number = episode.get('number', 0)
            ep_title = episode.get('title', 'Unknown Episode')

            embed.title = f"📺 {show_title} ({show_year})"
            description_lines.append(f"**Season {season} • Episode {number}**\n*{ep_title}*\n")

            poster_url = await get_tmdb_show_poster(show_title, show_year)

        # --- Progress Bar Logic ---
        started_at = playing.get('started_at')
        expires_at = playing.get('expires_at')

        if started_at and expires_at:
            start_time = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)

            total_duration = (end_time - start_time).total_seconds()
            elapsed = (now - start_time).total_seconds()

            if total_duration > 0:
                percent = min(max(elapsed / total_duration, 0), 1)

                def format_time(secs):
                    h, r = divmod(int(secs), 3600)
                    m, s = divmod(r, 60)
                    if h > 0: return f"{h}:{m:02d}:{s:02d}"
                    return f"{m}:{s:02d}"

                elapsed_str = format_time(elapsed)
                total_str = format_time(total_duration)

                bar_length = 14
                filled = int(percent * bar_length)
                bar = "▰" * filled + "▱" * (bar_length - filled)

                description_lines.append(f"`{elapsed_str}` {bar} `{total_str}`")

        if description_lines:
            embed.description = "\n".join(description_lines)

        embed.set_thumbnail(url=poster_url if poster_url else FALLBACK_POSTER)
        embed.set_footer(text="Scrobbling via Trakt.tv")
        embed.timestamp = datetime.now(timezone.utc)

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="top", description="Server-wide or Global Trakt leaderboard")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @commands.cooldown(1, 15, commands.BucketType.guild)
    async def leaderboard(self, ctx):
        top_users = get_leaderboard(limit=10)

        if not top_users:
            return await ctx.send(embed=error_embed("No users have registered their Trakt accounts yet!"))

        # <-- Make it DM safe by checking if ctx.guild exists
        location = ctx.guild.name if ctx.guild else "Global"

        embed = discord.Embed(
            title=f"🏆 {location} Watch Leaderboard",
            description="Top users ranked by total watched items.",
            color=discord.Color.gold()
        )

        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

        for index, row in enumerate(top_users):
            discord_id, username, movies, shows = row
            total = movies + shows

            # <-- Make it DM safe by using bot.get_user
            user = self.bot.get_user(int(discord_id))
            display_name = user.mention if user else f"**{username}**"

            embed.add_field(
                name=f"{medals[index]} {total:,} Total Scrobbles",
                value=f"{display_name} • 🎬 {movies:,} Movies | 📺 {shows:,} Shows",
                inline=False
            )

        embed.set_footer(text="Want to join? Use /tset to link your account!")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="profile", aliases=["tstats"],
                             description="View your detailed Trakt profile and stats")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    # <-- DM Safe Type Hinting
    async def profile_stats(self, ctx, member: Union[discord.Member, discord.User] = None):
        target_user = member or ctx.author
        username = get_user(target_user.id)

        if not username:
            return await ctx.send(embed=error_embed("No Trakt account linked."))

        loading_msg = await ctx.send(embed=discord.Embed(description="📊 Fetching profile data...", color=0xED1C24))

        try:
            db_movies, db_shows = count_total_scrobbles(username)
            api_stats = await get_user_stats(username)
            trakt_profile = await get_trakt_profile(username)

            avatar_url = target_user.display_avatar.url
            if trakt_profile and 'images' in trakt_profile:
                trakt_avatar = trakt_profile['images'].get('avatar', {}).get('full')
                if trakt_avatar and "gravatar.com" in trakt_avatar and "placeholders" not in trakt_avatar:
                    avatar_url = trakt_avatar

            embed = discord.Embed(color=0xED1C24)

            embed.set_author(
                name=f"{username}'s Trakt Stats",
                icon_url="https://walter.trakt.tv/hotlink-ok/public/favicon.ico",
                url=f"https://trakt.tv/users/{username}"
            )

            embed.set_thumbnail(url=avatar_url)

            if api_stats:
                movies_mins = api_stats.get('movies', {}).get('minutes', 0)
                shows_mins = api_stats.get('episodes', {}).get('minutes', 0)
                total_days = round((movies_mins + shows_mins) / 1440, 1)

                rank = "🌱 Casual Viewer"
                if total_days > 10: rank = "Popcorn Enthusiast"
                if total_days > 50: rank = "Couch Potato"
                if total_days > 150: rank = "Dedicated Cinephile"
                if total_days > 365: rank = "Screen Royalty"

                embed.description = f"🏆 **Rank:** {rank}\n━━━━━━━━━━━━━━━━━━━━"

                embed.add_field(
                    name="📽️ Watch Library\n━━━━━━━━━━━━━━━━━━━━",
                    value=(
                        f"🎬 **Movies:** {db_movies:,} `({round(movies_mins / 60):,} hrs)`\n"
                        f"📺 **Episodes:** {db_shows:,} `({round(shows_mins / 60):,} hrs)`\n"
                        f"⌛ **Total Time:** {total_days:,} Days"
                    ),
                    inline=False
                )

                ratings = api_stats.get('ratings', {}).get('total', 0)
                network = api_stats.get('network', {})
                followers = network.get('followers', 0)
                following = network.get('following', 0)

                embed.add_field(
                    name="\n 📊 Engagement\n━━━━━━━━━━━━━━━━━━━━",
                    value=f"⭐ {ratings:,} Ratings  •  👥 {followers:,} Followers  •  🗣️ {following:,} Following",
                    inline=False
                )

            await loading_msg.edit(embed=embed)

        except Exception as e:
            print(f"❌ CRASH in /profile: {e}")
            await loading_msg.edit(embed=error_embed("Failed to load profile. Check console."))


async def setup(bot):
    await bot.add_cog(SocialCog(bot))