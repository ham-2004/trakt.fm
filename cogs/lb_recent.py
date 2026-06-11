import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
from typing import Union

from config import FALLBACK_POSTER
from utils.embeds import error_embed, loading_embed
from utils.image_grid import create_titled_image_grid
from database.database import get_letterboxd_user
from api.letterboxd_api import get_letterboxd_diary, get_letterboxd_profile_stats, format_stars
from api.tmbd_api import get_tmdb_movie_poster

LETTERBOXD_COLOR = 0xFF8000

NOT_LINKED_EMBED = dict(
    title="Letterboxd Account Not Registered",
    description=(
        "You haven't linked your Letterboxd account yet.\n\n"
        "**Register:** Use `/lbset <username>` to link your account.\n"
        "**Need an account?** [Sign up here](https://letterboxd.com/create-account/)"
    )
)


async def resolve_poster(entry):
    """RSS poster -> TMDB fallback -> generic fallback."""
    poster_url = entry.get("poster_url")
    if not poster_url:
        poster_url = await get_tmdb_movie_poster(entry.get("title", ""), entry.get("year") or "")
    if not poster_url:
        poster_url = FALLBACK_POSTER
    elif not poster_url.startswith("http"):
        poster_url = "https://" + poster_url
    return poster_url


class LbRecentCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="lbr", description="Show your most recent Letterboxd diary entry")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def letterboxd_recent(self, ctx):
        username = get_letterboxd_user(ctx.author.id)

        if not username:
            await ctx.send(embed=error_embed(**NOT_LINKED_EMBED))
            return

        entries = await get_letterboxd_diary(username)
        if not entries:
            await ctx.send(embed=error_embed("No recent diary entries found."))
            return

        entry = entries[0]
        title = entry.get("title", "Unknown")
        year = entry.get("year") or "Unknown"

        raw_date = entry.get("watched_date", "")
        if raw_date:
            dt = datetime.strptime(raw_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            date = f"<t:{int(dt.timestamp())}:D>"
        else:
            date = "Unknown"

        lines = []
        stars = format_stars(entry.get("rating"))
        if stars:
            lines.append(f"⭐ {stars}")
        lines.append(f"🎬 Watched on {date}")
        if entry.get("rewatch"):
            lines.append("🔁 Rewatch")
        if entry.get("link"):
            lines.append(f"[Diary entry]({entry['link']})")

        embed = discord.Embed(
            title=f"📽️ Recent Letterboxd activity by {ctx.author.display_name}",
            url=f"https://letterboxd.com/{username}/films/diary/",
            color=LETTERBOXD_COLOR
        )
        embed.add_field(name=f"{title} ({year})", value="\n".join(lines), inline=False)
        embed.set_thumbnail(url=await resolve_poster(entry))

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="lb6", description="Show your 6 recent Letterboxd films in a grid image")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def letterboxd_six_recent(self, ctx):
        username = get_letterboxd_user(ctx.author.id)

        if not username:
            await ctx.send(embed=error_embed(**NOT_LINKED_EMBED))
            return

        loading_msg = await ctx.send(embed=loading_embed("Fetching films and generating grid..."))

        entries = await get_letterboxd_diary(username)
        if not entries:
            await loading_msg.edit(embed=error_embed("No recent diary entries found."))
            return

        grid_data = []
        for entry in entries[:6]:
            title = entry.get("title", "Unknown")
            year = entry.get("year") or "Unknown"
            grid_data.append((await resolve_poster(entry), f"{title} ({year})"))

        image_bytes = await create_titled_image_grid(grid_data)

        if not image_bytes:
            await loading_msg.edit(embed=error_embed("Failed to generate grid image."))
            return

        embed = discord.Embed(
            title=f"🎬 Recent Letterboxd Films for {ctx.author.display_name}",
            color=LETTERBOXD_COLOR,
            url=f"https://letterboxd.com/{username}/films/diary/"
        )
        embed.set_image(url="attachment://grid.webp")
        embed.set_footer(text=f"📔 Showing latest {len(grid_data)} of {len(entries)} recent diary entries")

        file = discord.File(image_bytes, filename="grid.webp")

        await loading_msg.delete()
        await ctx.send(embed=embed, file=file)

    @commands.hybrid_command(name="lbprofile", description="View your Letterboxd profile and stats")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def letterboxd_profile(self, ctx, member: Union[discord.Member, discord.User] = None):
        target_user = member or ctx.author
        username = get_letterboxd_user(target_user.id)

        if not username:
            return await ctx.send(embed=error_embed("No Letterboxd account linked."))

        loading_msg = await ctx.send(
            embed=discord.Embed(description="📊 Fetching profile data...", color=LETTERBOXD_COLOR))

        try:
            stats = await get_letterboxd_profile_stats(username)

            if not stats:
                await loading_msg.edit(embed=error_embed("Failed to load Letterboxd profile."))
                return

            embed = discord.Embed(color=LETTERBOXD_COLOR)
            embed.set_author(
                name=f"{stats.get('display_name') or username}'s Letterboxd Stats",
                icon_url="https://s.ltrbxd.com/static/img/icons/apple-touch-icon-152x152.png",
                url=f"https://letterboxd.com/{username}/"
            )
            embed.set_thumbnail(url=stats.get("avatar") or target_user.display_avatar.url)

            embed.add_field(
                name="📽️ Film Library\n━━━━━━━━━━━━━━━━━━━━",
                value=(
                    f"🎬 **Films:** {stats.get('films') or '?'}\n"
                    f"📅 **This Year:** {stats.get('this_year') or '?'}\n"
                    f"📝 **Lists:** {stats.get('lists') or '?'}"
                ),
                inline=False
            )

            embed.add_field(
                name="\n 📊 Network\n━━━━━━━━━━━━━━━━━━━━",
                value=(
                    f"👥 {stats.get('followers') or '?'} Followers  •  "
                    f"🗣️ {stats.get('following') or '?'} Following"
                ),
                inline=False
            )

            if stats.get("location"):
                embed.add_field(name="📍 Location", value=stats["location"], inline=False)

            await loading_msg.edit(embed=embed)

        except Exception as e:
            print(f"❌ CRASH in /lbprofile: {e}")
            await loading_msg.edit(embed=error_embed("Failed to load profile. Check console."))


async def setup(bot):
    await bot.add_cog(LbRecentCog(bot))
