import logging

from discord import Embed
from discord.ext import commands
from discord.ext.commands import Bot, Context, group, CommandError

from .blackjack.blackjack import Blackjack
from ..money.bank import Bank

logger = logging.getLogger(__name__)


class Arcade(commands.Cog, name="Games"):
    """Start and manage your favourite games"""

    def __init__(self, bot: Bot, bank: Bank):
        self.bot = bot
        self.bank = bank

    # noinspection PyUnusedLocal
    async def cog_command_error(self, ctx: Context, error: CommandError):
        logger.warning(f"Error in Arcade: {error}")

    @group(invoke_without_command=True)
    async def game(self, ctx: Context):
        """Handles game management"""
        pass

    @game.command()
    async def blackjack(self, ctx: Context, bet: int = 0):
        """Start a blackjack session"""
        view = Blackjack(ctx, self.bank, author_bet=bet)
        embed = Embed()
        embed.title = "Blackjack"
        msg = await ctx.send(embed=embed, view=view)
        await view.start_page(message=msg)
