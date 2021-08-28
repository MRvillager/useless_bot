import logging
from time import time
from typing import Union, Optional

import discord
from discord import Embed
from discord.ext import commands
from discord.ext.commands import Bot, group, Context, CommandError
from discord.utils import get

from .bank import Bank
from .errors import *

DAILY_CREDITS = 15
logger = logging.getLogger(__name__)


# TODO: add command to request refund
# TODO: add command to refresh user id cache


class BankInterface(commands.Cog, name="Bank"):
    """A discord-to-bank interface"""

    def __init__(self, bot: Bot, bank: Bank):
        self.bot = bot

        # bank init
        self.bank = bank

    async def cog_command_error(self, ctx: Context, error: CommandError):
        if isinstance(error, BalanceNotSufficientError):
            await ctx.reply(
                "Balance is not sufficient. Balance can't be negative",
                mention_author=False,
            )
        elif isinstance(error, InvalidUserID):
            await ctx.reply("User is invalid", mention_author=False)
        elif isinstance(error, UserIDNotRegistered):
            await ctx.reply(
                "User doesn't have a bank account. Use `-bank` to create one",
                mention_author=False,
            )
        elif isinstance(error, commands.BadArgument):
            await ctx.reply(
                "Passed arguments are not correct",
                mention_author=False,
            )
        elif isinstance(error, commands.CommandOnCooldown):
            m, s = divmod(error.retry_after, 60)
            h, m = divmod(m, 60)
            msg = f"{ctx.author.mention}, Try again in {round(h)} hours, {round(m)} minutes, and {round(s)} seconds."
            await ctx.reply(msg, mention_author=False)
        else:
            await ctx.reply("An error happened. Retry later", mention_author=False)
            logger.error(f"Error in BankCog: {error}")

    @staticmethod
    def gen_wait_str(seconds: int):
        seconds = 86400 - seconds
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)

        if hours > 0:
            return f"You need to wait {hours} hours"
        elif minutes > 0:
            return f"You need to wait {minutes} minutes"
        else:
            return f"You need to wait {seconds} seconds"

    @group(invoke_without_command=True, usage="")
    async def bank(self, ctx: Context, user: Optional[Union[discord.User, discord.Member]] = None):
        """Get your bank page"""
        if user is not None and ctx.author.guild_permissions.administrator:
            user_id = user.id
        else:
            user_id = ctx.author.id

        author_account = self.bank[user_id]
        seconds = int(time()) - author_account.last_free_credits

        if seconds > 86400:
            free_cr_text = f"Use `{ctx.prefix}bank free` to reclaim your free daily credits"
        else:
            free_cr_text = self.gen_wait_str(seconds)

        embed = Embed()
        embed.title = "Bank Status"
        embed.description = f"Bank status of <@{user_id}>"
        embed.add_field(
            name="Credits", value=f"`{author_account.balance}`", inline=False
        )
        embed.add_field(name="Free credits", value=free_cr_text, inline=False)

        await ctx.reply(embed=embed, mention_author=False)

    @bank.command()
    async def free(self, ctx: Context):
        """Get your daily free credits"""
        user_id = ctx.author.id
        author_account = self.bank[user_id]
        seconds = int(time()) - author_account.last_free_credits

        if seconds > 86400:
            self.bank.transaction(
                user_id=user_id, value=DAILY_CREDITS, reason="Free daily credits"
            )
            self.bank.update_last_free_credits(user_id=user_id, new_time=int(time()))
            await ctx.reply(
                f"Added {DAILY_CREDITS} credits to your account", mention_author=False
            )
        else:
            await ctx.reply(self.gen_wait_str(seconds), mention_author=False)

    @bank.command()
    async def transactions(self, ctx: Context,
                           limit: int = 5,
                           user: Optional[Union[discord.User, discord.Member]] = None):
        if user is not None and ctx.author.guild_permissions.administrator:
            user_id = user.id
        else:
            user_id = ctx.author.id

        embed = Embed()
        embed.title = "Transactions"
        embed.description = f"Transactions of <@{user_id}>"

        for transaction in self.bank.get_transactions(user_id, limit):
            text = f"Amount: {transaction.amount}"
            if transaction.reason is not None:
                text += f"\nReason: {transaction.reason}"
            if transaction.amount < 0 and transaction.refundable:
                text += f"\nIs refundable: Yes"
            text += f"\nDate: {transaction.date}"

            embed.add_field(name=f"#{transaction.token}", value=text, inline=False)

        await ctx.reply(embed=embed, mention_author=False)

    @bank.command()
    async def transaction(self, ctx: Context,
                          token: str,
                          user: Optional[Union[discord.User, discord.Member]] = None):
        if user is not None and ctx.author.guild_permissions.administrator:
            user_id = user.id
        else:
            user_id = ctx.author.id

        token = token.replace("#", "").upper()

        embed = Embed()
        embed.title = f"#{token}"
        embed.description = f"Transaction of <@{user_id}>"

        transaction = self.bank.get_transaction(user_id, token)
        embed.add_field(name=f"Amount", value=f"{transaction.amount}", inline=False)

        if transaction.reason is not None:
            reason = f"{transaction.reason}"
        else:
            reason = "Reason is not available"
        embed.add_field(name=f"Reason", value=reason, inline=False)

        if transaction.amount < 0 and transaction.refundable:
            refundable = "Yes"
        else:
            refundable = "No"
        embed.add_field(name=f"Refundable", value=refundable, inline=False)
        embed.add_field(name=f"Date", value=f"{transaction.date}", inline=False)

        await ctx.reply(embed=embed, mention_author=False)

    @commands.is_owner()
    @bank.command()
    async def add(self, ctx: Context, user: Union[discord.User, discord.Member], value: int):
        """Add some money to a user. WARNING: this will cause inflation"""
        self.bank.transaction(user_id=user.id, value=value, reason=f"Added to <@{user.id}> by <@{ctx.author.id}>")
        await ctx.reply(f"Added {value} credits to <@{user.id}>", mention_author=False)

    @commands.is_owner()
    @bank.command()
    async def remove(self, ctx: Context, user: Union[discord.User, discord.Member], value: int):
        """Remove money from a user. WARNING: this will cause inflation"""
        self.bank.transaction(user_id=user.id, value=-value, reason=f"Removed from <@{user.id}> by <@{ctx.author.id}>")
        await ctx.reply(f"Removed {value} credits from <@{user.id}>", mention_author=False)

    @commands.is_owner()
    @bank.command(hidden=True)
    async def cleanup(self, ctx: Context):
        members = list(self.bot.get_all_members())
        i = 0
        for user_id in self.bank.users:
            if get(members, id=user_id) is None:
                del self.bank[user_id]
                i += 1

        await ctx.reply(f"Bank database cleaned from {i} users")

    @commands.is_owner()
    @bank.command()
    async def reset(self, ctx: Context):
        self.bank.clear()
        await ctx.reply(f"Cleared database", mention_author=True)

    @bank.command()
    async def move(self, ctx: Context, user: Union[discord.User, discord.Member], value: int):
        value = abs(value)  # prevent money stealing
        self.bank.move(from_user=ctx.author.id, to_user=user.id, value=value)
        await ctx.reply(f"Moved {value} credits to <@{user.id}>", mention_author=False)
