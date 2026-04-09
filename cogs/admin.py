import discord
from discord.ext import commands
from typing import Literal, Optional  # <-- Required for the sync command!

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="reload", hidden=True)
    @commands.is_owner()
    async def reload_cog(self, ctx, extension: str):
        """Reloads a specific cog (e.g., !reload models.recent)"""
        try:
            if not extension.startswith("cogs."):
                extension = f"cogs.{extension}"

            await self.bot.reload_extension(extension)
            await ctx.send(f"✅ Successfully reloaded `{extension}`!")

        except commands.ExtensionNotLoaded:
            try:
                await self.bot.load_extension(extension)
                await ctx.send(f"✅ Successfully loaded new extension `{extension}`!")
            except Exception as e:
                await ctx.send(f"❌ Failed to load `{extension}`: ```py\n{e}```")

        except Exception as e:
            await ctx.send(f"❌ Failed to reload `{extension}`: ```py\n{e}```")

    @commands.command(name="sync", hidden=True)
    @commands.guild_only()
    @commands.is_owner()
    async def sync(
        self,
        ctx: commands.Context,
        guilds: commands.Greedy[discord.Object],
        spec: Optional[Literal["~", "*", "^"]] = None
    ) -> None:
        """Syncs the slash command tree."""
        if not guilds:
            if spec == "~":
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "*":
                ctx.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "^":
                ctx.bot.tree.clear_commands(guild=ctx.guild)
                await ctx.bot.tree.sync(guild=ctx.guild)
                synced = []
            else:
                synced = await ctx.bot.tree.sync()

            await ctx.send(
                f"✅ Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
            )
            return

        ret = 0
        for guild in guilds:
            try:
                await ctx.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                ret += 1

        await ctx.send(f"✅ Synced the tree to {ret}/{len(guilds)} servers.")


async def setup(bot):
    await bot.add_cog(AdminCog(bot))