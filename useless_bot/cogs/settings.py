import logging

from typing import TYPE_CHECKING, Optional
from discord.ext import commands
from discord.ext.commands import group, Context, CommandError

if TYPE_CHECKING:
    from .reddit import Reddit, Subreddit
    from .roles import Roles
    from .bank import Bank

logger = logging.getLogger(__name__)


class Settings(commands.Cog):
    """Manage bot settings"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.meme: Optional[Reddit] = self.bot.get_cog("Reddit")
        self.roles: Optional[Roles] = self.bot.get_cog("Roles")
        self.bank: Optional[Bank] = self.bot.get_cog("Bank")

    async def cog_check(self, ctx: Context):
        # Check if user is admin
        return ctx.author.guild_permissions.administrator

    async def cog_command_error(self, ctx: Context, error: CommandError):
        if isinstance(error, commands.BadArgument):
            await ctx.send("Passed arguments are not correct")
        else:
            await ctx.send("An error happened. Retry later")
            logger.error(f"Error in Settings: {error}")

    @group(invoke_without_command=True, hidden=True)
    async def settings(self, ctx: Context):
        """Handles global bot configuration"""

    @settings.group(invoke_without_command=True)
    async def roles(self, ctx: Context):
        """Handles roles configuration"""

    @settings.group(invoke_without_command=True)
    async def reddit(self, ctx: Context):
        """Handles reddit commands configuration"""

    @settings.group(invoke_without_command=True)
    async def bank(self, ctx: Context):
        """Handles bank configuration"""

    @bank.command()
    async def free(self, ctx: Context, free_credits: int):
        """Change the free daily quantity of credits"""
        if free_credits >= 0:
            await self.bank.config.set(["free_credits"], free_credits)
            await ctx.send(f"{free_credits} credits are the new daily free credits")
        else:
            await ctx.send("The value must be a positive integer", )

    @roles.command()
    async def price(self, ctx: Context, price: int):
        """Change the price for custom role creating"""
        if price >= 0:
            await self.roles.config.set(["price"], price)
            await ctx.send(f"{price} credits is the new price for Role buying")
        else:
            await ctx.send("The price must be a positive integer", )

    @reddit.command(aliases=["subreddits"], usage="<subreddits...>")
    async def nsfw(self, ctx: Context, *args: Subreddit):
        """Get or edit the current default subreddits for NSFW command"""
        if self.reddit is None:
            await ctx.send("Cannot change settings. Please restart this bot and report the bug")

        if len(args) != 0:
            await self.reddit.config.set(["nsfw_subreddits"], "+".join(args))

        current = self.reddit.config.get(["nsfw_subreddits"]).split('+')
        await ctx.send(f"NSFW subreddits: r/{' r/'.join(current)}")

    @reddit.command(aliases=["subreddits"], usage="<subreddits...>")
    async def meme(self, ctx: Context, *args: Subreddit):
        """Get or edit the current default subreddits for Meme command"""
        if self.reddit is None:
            await ctx.send("Cannot change settings. Please restart this bot and report the bug")

        if len(args) != 0:
            await self.reddit.config.set(["subreddits"], "+".join(args))

        current = self.reddit.config.get(["subreddits"]).split('+')
        await ctx.send(f"Meme subreddits: r/{' r/'.join(current)}")
