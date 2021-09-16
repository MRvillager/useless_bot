import logging

from discord import Member, TextChannel
from discord.ext import commands
from discord.ext.commands import Bot, Context, CommandError, check

from useless_bot.core.config import Config
from useless_bot.core.drivers import Shelve
from useless_bot.utils import is_admin
from .views import WarnLimit

logger = logging.getLogger(__name__)

schema = {
    "stalk_users": [],
    "leave_msg": "{} has left the server",
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

        self._config = Config(cog="General", driver=Shelve(), schema=schema)

        self.meme = self.bot.get_cog("Meme")
        self.sauce = self.bot.get_cog("Sauce")

    async def cog_command_error(self, ctx: Context, error: CommandError):
        if isinstance(error, commands.BadArgument):
            await ctx.send("Passed arguments are not correct", )
        else:
            await ctx.send("An error happened. Retry later")
            logger.error(f"Error in Management: {error}")

    @commands.Cog.listener()
    async def on_member_remove(self, member: Member):
        channel: TextChannel = member.guild.system_channel
        leave_msg = await self._config.get(["leave_msg"])
        await channel.send(leave_msg.format(member.mention))

    @commands.Cog.listener()
    async def on_member_update(self, before: Member, after: Member):
        """Send a message in system channel when a stalked member is not more offline"""
        stalk_users = await self._config.get(["stalk_users"])
        if not stalk_users:
            return

        if before.id not in stalk_users:
            return

        if before.status == after.status:
            return

        channel: TextChannel = after.guild.system_channel
        await channel.send(f"The user {after.mention} is now online")

        # remove user from stalk list after he is online
        await self._config.delete(["stalk_users", before.id])

    @check(is_admin)
    @commands.command()
    async def ban(self, ctx: Context, user: Member, reason: str):
        """Ban a user"""
        await user.ban(reason=reason)
        await ctx.send(f"Banned {user.mention}")

    @check(is_admin)
    @commands.command()
    async def kick(self, ctx: Context, user: Member, reason: str):
        """Kick a user"""
        await user.ban(reason=reason)
        await ctx.send(f"Kicked {user.mention}")

    @check(is_admin)
    @commands.command()
    async def warn(self, ctx: Context, user: Member):
        """Warn a user and, ban or kick him if he reached"""
        warns_count = await self._config.get(["warn", "users", user.id])
        warns_count += 1
        warns_count = await self._config.set(["warn", "users", user.id], warns_count)

        if warns_count >= await self._config.get(["warn", "settings", "count"]):
            view = WarnLimit(user)
            await ctx.send(f"Warn limit reached for {user.mention}.\nDo you want to ban or kick the user?\n"
                           "Do nothing to reset the user's warn count", view=view)
            await view.wait()
            if not view:
                await self._config.set(["warn", "users", user.id], 0)

    @check(is_admin)
    @commands.command()
    async def stalk(self, ctx: Context, user: Member):
        """Stalk a user, and send a message in the system channel when that user is online"""
        users = await self._config.get(["stalk_users"])
        if user.id in users:
            await self._config.delete(["stalk_users", user.id])
            await ctx.send(f"Stalking for {user.mention} removed")
        else:
            await self._config.set(["stalk_users"], users.append(user.id))
            await ctx.send(f"Stalking for {user.mention} started")

    @commands.command()
    async def echo(self, ctx: Context, message: str):
        """Print the raw content of a message"""
        if "stupid" in message:
            await ctx.send(f"Yeah we already know")
        else:
            await ctx.send(f"`{message}`")
