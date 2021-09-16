import logging

from discord import Embed
from discord.ext import commands
from discord.ext.commands import Bot, Context, group, CommandError

from useless_bot.core.bank_core import BankCore
from .blackjack import Blackjack

logger = logging.getLogger(__name__)


class Arcade(commands.Cog, name="Games"):
    """Start and manage your favourite games"""

    def __init__(self, bot: Bot, bank: BankCore):
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
    async def blackjack(self, ctx: Context):
        """
        Start a blackjack session
        To play this game you will need 5 credits
        """
        view = Blackjack(ctx, self.bank)
        embed = Embed()
        embed.title = "Blackjack"
        msg = await ctx.send(embed=embed, view=view)
        await view.start_page(message=msg)
