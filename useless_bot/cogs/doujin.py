import logging
import re
import aiohttp

from typing import Optional
from discord import Embed
from discord.ext import commands
from discord.ext.commands import Bot, is_nsfw, Context

logger = logging.getLogger(__name__)


class Code(commands.Converter, str):
    async def convert(self, _: Context, argument: str) -> str:
        if argument.isdecimal():
            raise TypeError("A code must be an integer")
        elif len(argument) != 6:
            raise TypeError("A code must have 6 digits")

        return argument


class Doujin(commands.Cog):
    def __init__(self, discord_bot: Bot, connector: aiohttp.BaseConnector):
        self.bot = discord_bot

        self.session = aiohttp.ClientSession(loop=self.bot.loop,
                                             connector=connector)

    async def cog_command_error(self, ctx: Context, error: Exception) -> None:
        if isinstance(error, commands.BadArgument):
            await ctx.send("Passed arguments are not correct")
        else:
            await ctx.send("An error happened. Retry later")
            logger.error(f"Error in Settings: {error}")

    @is_nsfw()
    @commands.command()
    async def doujin(self, ctx: Context, code: Optional[Code] = None):
        """Get random ragu from doujin.net"""
        if code:
            url = f"https://nhentai.net/g/{code}"
            logger.info(f"Retrieving {code} from nhentai.net")
            async with self.session.get(url, allow_redirects=False) as resp:
                content = await resp.text()
        else:
            logger.info(f"Retrieving random page from nhentai.net")
            async with self.session.get("https://nhentai.net/random", allow_redirects=True) as resp:
                url = str(resp.url)
                content = await resp.text()
            code = url.split("/")[-2]
        logger.info(f"Retrieved {code} from nhentai.net")

        logger.debug("Creating embed")
        embed = self.create_embed(url, code, content)
        logger.debug("Embed created")
        await ctx.send(embed=embed)

    @staticmethod
    def create_embed(url: str, code: str, content: str) -> Embed:
        cover = re.search("([0-9]+)(/cover.[a-zA-Z]+)", content)

        embed = Embed()
        embed.set_image(url=f"https://i.nhentai.net/galleries/{cover.group(1)}/1.jpg")
        embed.title = f"#{code}"
        embed.description = f"Here is your [sauce]({url})"

        return embed
