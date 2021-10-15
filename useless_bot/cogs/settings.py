import logging
from typing import Optional

from nextcord.ext import commands
from nextcord.ext.commands import group, Context, CommandError

from useless_bot.utils import on_global_command_error
from .bank import Bank
from .general import General
from .reddit import Reddit, Subreddit
from .roles import Roles

logger = logging.getLogger("useless_bot.cog.settings")


class Settings(commands.Cog):
    """Manage bot settings"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.reddit_cog: Optional[Reddit] = self.bot.get_cog("Reddit")
        self.roles_cog: Optional[Roles] = self.bot.get_cog("Roles")
        self.bank_cog: Optional[Bank] = self.bot.get_cog("Bank")
        self.general_cog: Optional[General] = self.bot.get_cog("General")
        self.arcade_cog: Optional[General] = self.bot.get_cog("Arcade")

    async def cog_check(self, ctx: Context):
        # Check if user is admin
        return ctx.author.guild_permissions.administrator

    async def cog_command_error(self, ctx: Context, error: CommandError):
        if not await on_global_command_error(ctx, error):
            logger.error(f"Exception occurred", exc_info=True)

    @group(invoke_without_command=True)
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

    @settings.group(invoke_without_command=True)
    async def arcade(self, ctx: Context):
        """Handles arcade configuration"""

    @settings.command(invoke_without_command=True)
    async def leave(self, ctx: Context, *, message: str):
        """Change leave message"""
        await self.general_cog.config.set(["leave_msg"], message)
        await ctx.send(f"New leave message set\nExample: " + message.format(ctx.author.mention))

    @arcade.command()
    async def blackjack(self, ctx: Context, bet: int):
        if bet < 0:
            await ctx.send("The bet must be a positive integer")
            return

        await self.arcade_cog.config.set(["blackjack"], bet)
        await ctx.send(f"The new bet is now {bet}")

    @bank.command()
    async def free(self, ctx: Context, free_credits: int):
        """Change the free daily quantity of credits"""
        if free_credits >= 0:
            await self.bank_cog.config.set(["free_credits"], free_credits)
            await ctx.send(f"{free_credits} credits are the new daily free credits")
        else:
            await ctx.send("The value must be a positive integer", )

    @roles.command()
    async def price(self, ctx: Context, price: int):
        """Change the price for custom role creating"""
        if price >= 0:
            await self.roles_cog.config.set(["price"], price)
            await ctx.send(f"{price} credits is the new price for Role buying")
        else:
            await ctx.send("The price must be a positive integer", )

    @reddit.command(usage="<subreddits...>")
    async def nsfw(self, ctx: Context, subreddits: commands.Greedy[Subreddit]):
        """Get or edit the current default subreddits for NSFW command"""
        if self.reddit_cog is None:
            await ctx.send("Cannot change settings. Please restart this bot and report the bug")

        if len(subreddits) != 0:
            await self.reddit_cog.config.set(["nsfw_subreddits"], "+".join(subreddits))

        current = await self.reddit_cog.config.get(["nsfw_subreddits"])
        current = current.split('+')
        await ctx.send(f"NSFW subreddits: r/{' r/'.join(current)}")

    @reddit.command(usage="<subreddits...>")
    async def meme(self, ctx: Context, subreddits: commands.Greedy[Subreddit]):
        """Get or edit the current default subreddits for Meme command"""
        if self.reddit_cog is None:
            await ctx.send("Cannot change settings. Please restart this bot and report the bug")

        if len(subreddits) != 0:
            await self.reddit_cog.config.set(["subreddits"], "+".join(subreddits))

        current = await self.reddit_cog.config.get(["subreddits"])
        current = current.split('+')
        await ctx.send(f"Meme subreddits: r/{' r/'.join(current)}")
