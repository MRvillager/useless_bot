import logging
import re

import aiohttp
from discord import Embed
from discord.ext import commands
from discord.ext.commands import Context, Bot, is_nsfw

from .interface import RedditCog
from .reddit import RedditLister
from ..money.bank import Bank
from ..money.errors import UserIDNotRegistered, BalanceNotSufficientError

logger = logging.getLogger(__name__)


class Sauce(RedditCog):
    """Get some NSFW amatriciana"""

    def __init__(self, discord_bot: Bot, reddit_bot: RedditLister, bank: Bank, connector: aiohttp.BaseConnector):
        self.bot = discord_bot
        self.bank = bank

        subreddits = "Hornyjail"

        super(Sauce, self).__init__(
            reddit_bot=reddit_bot, subreddits=subreddits, discord_bot=discord_bot
        )

        self.config.setdefault("sauce_cost", 1)
        self.session = aiohttp.ClientSession(loop=self.bot.loop,
                                             connector=connector)
        self.post_cache = 30

    async def cog_before_invoke(self, ctx: Context):
        if self.config["sauce_cost"] >= 1:
            self.bank.transaction(
                user_id=ctx.author.id, value=-self.config["sauce_cost"], reason="The user bought some sauce"
            )

    async def cog_command_error(self, ctx: Context, error: str):
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
            await ctx.reply("An error happened. Retry later", mention_author=False)
            logger.error(f"Error in Sauce: {error}")

    def unload(self):
        self.bot.loop.run_until_complete(self.session.close())

    @is_nsfw()
    @commands.command(usage="[subreddits...]")
    async def sauce(self, ctx: Context, *args: str):
        """Get some pesto from NSFW subreddits"""
        await self.base_command(ctx, *args)

    @is_nsfw()
    @commands.command()
    async def random(self, ctx: Context):
        """Get random ragu from nhentai.net"""
        # check if channel is in whitelist
        if not await self.check_whitelist(ctx):
            return

        async with self.session.get("https://nhentai.net/random", allow_redirects=True) as resp:
            url = str(resp.url)
            content = await resp.text()
        num = url.split("/")[-2]
        cover = re.search("([0-9]+)(/cover.[a-zA-Z]+)", content)

        embed = Embed()
        embed.set_image(url=f"https://i.nhentai.net/galleries/{cover.group(1)}/1.jpg")
        embed.description = f"So you feel lucky today, here is your [sauce]({url}).\nNumber: " f"{num}"

        await ctx.reply(embed=embed, mention_author=False)
