import logging

from discord import Embed
from discord.ext import commands
from discord.ext.commands import Bot, Context, group, CommandError

from useless_bot.core.bank_core import BankCore
from useless_bot.core.config import Config
from useless_bot.core.drivers import Shelve
from useless_bot.utils import on_global_command_error
from .blackjack import Blackjack

logger = logging.getLogger("useless_bot.cog.arcade")

schema = {"blackjack": 5}


class Arcade(commands.Cog, name="Games"):
    """Start and manage your favourite games"""

    def __init__(self, bot: Bot, bank: BankCore):
        self.bot = bot
        self.bank = bank

        self.config = Config(cog="Arcade", driver=Shelve(), schema=schema)

    # noinspection PyUnusedLocal
    async def cog_command_error(self, ctx: Context, error: CommandError):
        if not await on_global_command_error(ctx, error):
            logger.error(f"Exception occurred", exc_info=True)

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
        bet: int = await self.config.get(["blackjack"])
        view = Blackjack(ctx, self.bank, bet)
        embed = Embed()
        embed.title = "Blackjack"
        msg = await ctx.send(embed=embed, view=view)
        await view.start_page(message=msg)
