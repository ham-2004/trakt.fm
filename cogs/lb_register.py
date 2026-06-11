import discord
from discord.ext import commands
from discord import app_commands

from database.database import save_letterboxd_user, get_letterboxd_user, delete_letterboxd_user
from api.letterboxd_api import letterboxd_user_exists
from utils.embeds import error_embed, success_embed


class LbRegisterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="lbset", description="Link your Letterboxd account to the bot")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def letterboxd_register(self, ctx, username: str):
        await ctx.defer()

        if not await letterboxd_user_exists(username):
            await ctx.send(embed=error_embed(
                title="Invalid Letterboxd Username",
                description=f"The username `{username}` does not exist on [Letterboxd](https://letterboxd.com)."
            ))
            return

        save_letterboxd_user(ctx.author.id, username)

        await ctx.send(embed=success_embed(
            title="Letterboxd Account Linked",
            description=f"[**{username}**](https://letterboxd.com/{username}/) has been linked to {ctx.author.mention}!"
        ))

    @commands.hybrid_command(name="lbunlink", description="Unlink your Letterboxd account from the bot")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def letterboxd_unlink(self, ctx):
        username = get_letterboxd_user(ctx.author.id)

        if not username:
            return await ctx.send(
                embed=error_embed("You don't have a Letterboxd account linked. Nothing to unlink!")
            )

        delete_letterboxd_user(ctx.author.id)

        await ctx.send(
            embed=success_embed(
                f"Your Letterboxd account **{username}** has been unlinked.\n"
                f"You can re-link anytime with `/lbset <username>`.",
                title="Account Unlinked"
            )
        )


async def setup(bot):
    await bot.add_cog(LbRegisterCog(bot))
