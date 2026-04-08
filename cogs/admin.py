import discord
from discord.ext import commands


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


async def setup(bot):
    await bot.add_cog(AdminCog(bot))