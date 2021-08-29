from __future__ import annotations

import logging

from discord import Member, Guild, Role, Color
from discord.ext import commands
from discord.ext.commands import Bot, Context, group, check

from ..config import Config
from ..money.bank import Bank
from ..money.errors import BalanceNotSufficientError, UserIDNotRegistered
from ..utils import is_admin

logger = logging.getLogger(__name__)


class Roles(commands.Cog):
    def __init__(self, bot: Bot, bank: Bank):
        self.bot = bot
        self.bank = bank

        self.name = self.__class__.__name__

        self.config = Config(self.name)
        self.config.setdefault("create_role_price", 75)

    async def cog_command_error(self, ctx: Context, error: str):
        # Handle the errors from the cog here
        if isinstance(error, BalanceNotSufficientError):
            await ctx.reply(
                "Balance is not sufficient. Balance can't be negative",
                mention_author=False,
            )
        elif isinstance(error, UserIDNotRegistered):
            await ctx.reply(
                "User doesn't have a bank account. Use `-bank` to create one",
                mention_author=False,
            )
        else:
            logger.error(f"Error in Roles: {error}")

    @group(invoke_without_command=True, hidden=True)
    async def roles(self, ctx: Context):
        """Handles roles commands"""
        pass

    @roles.command()
    async def create(self, ctx: Context, name: str, color: Color = None):
        """Create a role for an amount of credits"""
        if self.config["create_role_price"] > 0:
            try:
                self.bank.transaction(
                    user_id=ctx.author.id, value=-self.config["create_role_price"],
                    reason=f"The user bought the role {name}"
                )
            except (BalanceNotSufficientError, UserIDNotRegistered):
                await ctx.reply("Cannot get the money from your account")
                return

        if color is None:
            color = Color.random()

        guild: Guild = ctx.guild
        author: Member = ctx.author

        role = await guild.create_role(
            name=name, color=color, reason=f"<@{author.id}> has requested it"
        )
        await author.add_roles(role, reason=f"<@{author.id}> has requested it")
        await ctx.reply(
            f"Role <@&{role.id}> create and added to <@{author.id}>",
            mention_author=False,
        )

    @roles.command()
    @check(is_admin)
    async def color(self, ctx: Context, role: Role, color: Color = None):
        """Change color to a role"""
        if color is None:
            color = Color.random()

        await role.edit(color=color)
        await ctx.reply(f"Changed color to <@&{role.id}>", mention_author=False)

    @roles.command()
    @check(is_admin)
    async def delete(self, ctx: Context, role: Role):
        """Delete a role"""
        await ctx.reply(f"Deleted <@&{role.id}>", mention_author=False)
        await role.delete(reason="<@{ctx.author.id}> has requested it")
