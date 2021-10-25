import logging
from random import randint
from string import ascii_lowercase, digits
from typing import List, Iterable

from aiohttp.web_exceptions import HTTPException
from nextcord import Embed
from nextcord.ext import commands
from nextcord.ext.commands import Bot, Context, is_nsfw, CommandError

from useless_bot.core.config import Config
from useless_bot.core.reddit_api import RedditAPI, Post, Forbidden
from useless_bot.utils import on_global_command_error

__all__ = ["Reddit"]

logger = logging.getLogger("useless_bot.cog.reddit")
schema = {
    "subreddits": "memes+dankmemes",
    "nsfw_subreddits": "hornyjail"
}


class Subreddit(commands.Converter):
    whitelist = ascii_lowercase + digits + "_"

    async def convert(self, _: Context, argument: str) -> str:
        argument = argument.removeprefix("r/")
        if len(argument) not in range(3, 22):
            raise TypeError("A subreddit can have at minimum 3 characters and maximum 21 characters")

        if any(c not in self.whitelist for c in argument) or argument[0] == "_":
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
        self.config = Config(cog="Reddit", schema=schema)

    async def cog_command_error(self, ctx: Context, error: CommandError) -> None:
        if isinstance(error, Forbidden):
            await ctx.send("One or all subreddits cannot be accessed")
        elif isinstance(error, HTTPException):
            await ctx.send("There is a problem with Reddit API. Try again later")
        else:
            if not await on_global_command_error(ctx, error):
                logger.error(f"Exception occurred", exc_info=True)

    @commands.command()
    async def link(self, ctx: Context, *, url: str):
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
    @commands.command(usage="[subreddits...]", aliases=["sauce"])
    async def nsfw(self, ctx: Context, subreddits: commands.Greedy[Subreddit] = None):
        """Get NSFW post from Reddit"""
        if subreddits:
            post = await self.get_post_from_subreddit(subreddits)
        else:
            if len(self.nsfw_cache) == 0:
                await self.refresh_nsfw()

            post = self.nsfw_cache.pop(randint(0, len(self.nsfw_cache) - 1))

        await ctx.send(embed=self.create_embed(post))

    async def refresh_nsfw(self):
        logger.info(f"Refreshing nsfw submissions cache")
        subreddits = await self.config.get(["nsfw_subreddits"])
        self.nsfw_cache = await self.reddit.hot(subreddits)
        logger.info(f"Refresh complete")

    @commands.command(usage="[subreddits...]")
    async def meme(self, ctx: Context, subreddits: commands.Greedy[Subreddit] = None):
        """Get a safe post from Reddit"""
        if subreddits:
            post = await self.get_post_from_subreddit(subreddits)

            if post.is_nsfw:
                await ctx.send("The retrieved post is NSFW. Use the nsfw command for NSFW post")
                return
        else:
            if len(self.meme_cache) == 0:
                await self.refresh_meme()

            post = self.meme_cache.pop(randint(0, len(self.meme_cache) - 1))

        await ctx.send(embed=self.create_embed(post))

    async def refresh_meme(self):
        logger.info(f"Refreshing meme submissions cache")
        subreddits = await self.config.get(["subreddits"])
        self.meme_cache = await self.reddit.hot(subreddits)
        logger.info(f"Refresh complete")

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
        # noinspection PyTypeChecker
        post_list = await self.reddit.hot(subreddit, limit=5)
        return post_list[randint(0, 4)]

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
