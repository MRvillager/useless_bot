from __future__ import annotations

import logging

from discord import Member, Guild, Role, Color
from discord.ext import commands
from discord.ext.commands import Bot, Context, group, check

from useless_bot.core.bank_core import BankCore
from useless_bot.core.config import Config
from useless_bot.core.drivers import Shelve
from useless_bot.core.errors import BalanceUnderLimitError, BalanceOverLimitError
from useless_bot.utils import is_admin

schema = {"create_role_price": 75}

logger = logging.getLogger(__name__)


class Roles(commands.Cog):
    def __init__(self, bot: Bot, bank: BankCore):
        self.bot = bot
        self.bank = bank

        self.config = Config(cog="Roles", driver=Shelve(), schema=schema)

    async def cog_command_error(self, ctx: Context, error: str):
        # Handle the errors from the cog here
        if isinstance(error, BalanceUnderLimitError):
            await ctx.send("You don't have enough credits")
        elif isinstance(error, BalanceOverLimitError):
            await ctx.send("You have too much credits")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Passed arguments are not correct")
        else:
            await ctx.send("An error happened. Retry later")
            logger.error(f"Error in Roles: {error}")

    @group(invoke_without_command=True, hidden=True)
    async def roles(self, ctx: Context):
        """Handles roles commands"""
        pass

    @roles.command()
    async def create(self, ctx: Context, name: str, color: Color = None):
        """Create a role for an amount of credits"""
        role_price = await self.config.get(["create_role_price"])
        if role_price > 0:
            await self.bank.withdraw(user=ctx.author, value=role_price)

        if color is None:
            color = Color.random()

        guild: Guild = ctx.guild
        author: Member = ctx.author

        role = await guild.create_role(
            name=name, color=color, reason=f"{author.mention} has requested it"
        )
        await author.add_roles(role, reason=f"{author.mention}has requested it")
        await ctx.send(
            f"Role {role.mention} create and added to {author.mention}",
            mention_author=False,
        )

    @roles.command()
    @check(is_admin)
    async def color(self, ctx: Context, role: Role, color: Color = None):
        """Change color to a role"""
        if color is None:
            color = Color.random()

        await role.edit(color=color)
        await ctx.send(f"Changed color to {role.mention}")

    @roles.command()
    @check(is_admin)
    async def delete(self, ctx: Context, role: Role):
        """Delete a role"""
        await ctx.send(f"Deleted {role.mention}")
        await role.delete(reason=f"{ctx.author.mention} has requested it")
