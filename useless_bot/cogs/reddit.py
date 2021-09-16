import logging

from random import randint
from string import ascii_lowercase, digits
from typing import List, Iterable, Optional
from aiohttp.web_exceptions import HTTPException
from discord import Embed
from discord.ext import commands
from discord.ext.commands import Bot, Context, is_nsfw
from yarl import URL

from useless_bot.core.config import Config
from useless_bot.core.drivers import Shelve
from useless_bot.core.reddit_api import RedditAPI, Post, Forbidden

logger = logging.getLogger(__name__)


class Subreddit(commands.Converter, str):
    whitelist = ascii_lowercase + digits + "_"

    async def convert(self, _: Context, argument: str) -> str:
        argument = argument.removesuffix("r/")
        if len(argument) not in range(3, 22):
            raise TypeError("A subreddit can have at minimum 3 characters and maximum 21 characters")

        if any(argument) not in self.whitelist or argument[0] == "_":
            raise TypeError("The name of the subreddit must consist of 3 to 21 upper or lowercase Latin characters, "
                            "digits, or underscores (but the first character can't be an underscore). No spaces.")

        return argument


class Reddit(commands.Cog):
    def __init__(self, discord_bot: Bot, reddit_api: RedditAPI):
        self.reddit = reddit_api
        self.discord_bot = discord_bot

        self.meme_cache: list[Post] = []
        self.nsfw_cache: list[Post] = []

        # init/load cog config
        self.config = Config(cog="Reddit", driver=Shelve())

        self.config.setdefault(["subreddits"], "memes+dankmemes")
        self.config.setdefault(["nsfw_subreddits"], "hornyjail")

    async def cog_command_error(self, ctx: Context, error: Exception) -> None:
        if isinstance(error, Forbidden):
            await ctx.send("One or all subreddits cannot be accessed")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Passed arguments are not correct")
        elif isinstance(error, HTTPException):
            await ctx.send("There is a problem with Reddit API. Try again later")
        else:
            await ctx.send("An error happened. Retry later")
            logger.error(f"Error in Settings: {error}")

    @commands.command()
    async def link(self, ctx: Context, url: URL):
        """Send a post from a reddit link"""
        post = await self.reddit.link(url)

        if post.is_nsfw:
            if ctx.channel.is_nsfw():
                await ctx.send(embed=self.create_embed(post))
            else:
                await ctx.send("Cannot send a NSFW post in a no-NSFW channel")
        else:
            await ctx.send(embed=self.create_embed(post))

    @is_nsfw()
    @commands.command(usage="[subreddits...]")
    async def nsfw(self, ctx: Context, subreddit: Optional[Subreddit] = None):
        """Get NSFW post from Reddit"""
        if subreddit:
            post = await self.get_post_from_subreddit(subreddit)
        else:
            if len(self.nsfw_cache) == 0:
                logger.info(f"Refreshing nsfw submissions cache")
                subreddits = await self.config.get(["nsfw_subreddits"])
                self.nsfw_cache = await self.reddit.hot(subreddits)
                logger.info(f"Refreshing complete")

            post = self.nsfw_cache.pop(randint(0, len(self.nsfw_cache) - 1))

        await ctx.send(embed=self.create_embed(post))

    @commands.command(usage="[subreddits...]")
    async def meme(self, ctx: Context, subreddit: Optional[Subreddit] = None):
        """Get a safe post from Reddit"""
        if subreddit:
            post = await self.get_post_from_subreddit(subreddit)
        else:
            if len(self.meme_cache) == 0:
                logger.info(f"Refreshing meme submissions cache")
                subreddits = await self.config.get(["subreddits"])
                self.meme_cache = await self.reddit.hot(subreddits)
                logger.info(f"Refreshing complete")

            post = self.meme_cache.pop(randint(0, len(self.meme_cache) - 1))

        if post.is_nsfw:
            await ctx.send("The retrieved post is NSFW. Use the nsfw command for NSFW post")
        else:
            await ctx.send(embed=self.create_embed(post))

    async def change_meme_source(self, subreddits: List[str]):
        # parse subreddits and save them
        await self.config.set(["subreddits"], self.parse_subreddits(subreddits))
        # empty cache with new subreddits
        self.meme_cache = []

    async def change_nsfw_source(self, subreddits: List[str]):
        # parse subreddits and save them
        await self.config.set(["nsfw_subreddits"], self.parse_subreddits(subreddits))
        # empty cache with new subreddits
        self.nsfw_cache = []

    async def get_post_from_subreddit(self, subreddit: Subreddit):
        post_list = await self.reddit.hot(subreddit, limit=5)
        return post_list[0]

    @staticmethod
    def parse_subreddits(subreddits: Iterable[str]):
        return "+".join([subreddit.removesuffix("r/") for subreddit in subreddits])

    @staticmethod
    def create_embed(post: Post) -> Embed:
        # Create embed
        embed = Embed()
        # set properties
        embed.title = post.title
        embed.url = post.link
        embed.description = post.subreddit

        embed.set_author(name=post.author)
        embed.set_image(url=post.media)

        return embed

    def cog_unload(self):
        self.discord_bot.loop.run_until_complete(self.reddit.close())
