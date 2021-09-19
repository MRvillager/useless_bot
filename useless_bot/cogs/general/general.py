import logging

from discord import Member, TextChannel
from discord.ext import commands
from discord.ext.commands import Bot, Context, CommandError, has_permissions, bot_has_permissions

from useless_bot.core.config import Config
from useless_bot.core.drivers import Shelve
from useless_bot.utils import on_global_command_error
from .views import WarnLimit

logger = logging.getLogger("useless_bot.cog.general")

schema = {
    "leave_msg": "{mention} has left the server",
    "warn": {
        "settings": {
            "count": 5
        },
        "users": {}
    }
}


class General(commands.Cog):
    """Manages sensitive elements of the bot"""

    def __init__(self, bot: Bot):
        self.bot = bot

        self.config = Config(cog="General", driver=Shelve(), schema=schema)

        self.meme = self.bot.get_cog("Meme")
        self.sauce = self.bot.get_cog("Sauce")

    async def cog_command_error(self, ctx: Context, error: CommandError):
        if not await on_global_command_error(ctx, error):
            logger.error(f"Exception occurred", exc_info=True)

    @commands.Cog.listener()
    async def on_member_remove(self, member: Member):
        channel: TextChannel = member.guild.system_channel
        leave_msg = await self.config.get(["leave_msg"])
        await channel.send(leave_msg.format(mention=member.mention))

    @commands.command()
    @commands.guild_only()
    @bot_has_permissions(administrator=True, ban_members=True)
    @has_permissions(ban_members=True)
    async def ban(self, ctx: Context, user: Member, *, reason: str):
        """Ban a user"""
        await user.ban(reason=reason)
        await ctx.send(f"Banned {user.mention}")

    @commands.command()
    @commands.guild_only()
    @bot_has_permissions(administrator=True, kick_members=True)
    @has_permissions(kick_members=True)
    async def kick(self, ctx: Context, user: Member, *, reason: str):
        """Kick a user"""
        await user.kick(reason=reason)
        await ctx.send(f"Kicked {user.mention}")

    @commands.command()
    @commands.guild_only()
    @bot_has_permissions(administrator=True, ban_members=True, kick_members=True)
    @has_permissions(administrator=True)
    async def warn(self, ctx: Context, user: Member):
        """Warn a user and, ban or kick him if he reached"""
        try:
            warns_count = await self.config.get(["warn", "users", user.id])
        except KeyError:
            warns_count = 0
        warns_count += 1
        await self.config.set(["warn", "users", user.id], warns_count)

        if warns_count >= await self.config.get(["warn", "settings", "count"]):
            view = WarnLimit(user)
            await ctx.send(f"Warn limit reached for {user.mention}.\nDo you want to ban or kick the user?\n"
                           "Do nothing to reset the user's warn count", view=view)
            await view.wait()
            if not view:
                await self.config.set(["warn", "users", user.id], 0)
        else:
            await ctx.send(f"{user.mention} has now {warns_count} warn(s)")

    @commands.command()
    async def echo(self, ctx: Context, *, message: str):
        """Print the raw content of a message"""
        if "stupid" in message:
            await ctx.send(f"Yeah we already know")
        else:
            await ctx.send(f"{message}")
