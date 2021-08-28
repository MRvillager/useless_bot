import logging
from random import randint
from typing import List

from aiohttp.web_exceptions import HTTPException
from discord import Embed
from discord.ext import commands
from discord.ext.commands import Bot, Context

from .reddit import RedditLister, Post, Forbidden
from ..config import Config

logger = logging.getLogger(__name__)


class RedditCog(commands.Cog):
    def __init__(self, reddit_bot: RedditLister, discord_bot: Bot, subreddits: str):
        # temp vars
        self.name = self.__class__.__name__
        self.reddit = reddit_bot
        self.discord_bot = discord_bot
        self.posts: list[Post] = []

        # config vars
        self.config = Config(name=self.name)

        self.config.setdefault("subreddits", subreddits)
        self.config.setdefault("whitelist", [])

    def cog_unload(self):
        self.discord_bot.loop.run_until_complete(self.reddit.close())
        self.unload()

    def unload(self):
        pass

    async def base_command(self, ctx: Context, *args: str):
        # check if channel is in whitelist
        if not await self.check_whitelist(ctx):
            return

        if len(args) != 0:
            subreddits = [subreddit.replace("r/", "") for subreddit in args]
            subreddits_str = "+".join(subreddits)
            await self.send_from_reddit(ctx, subreddits_str)
        else:
            await self.send_from_reddit(ctx)

    async def source(self, subreddits: List[str]):
        sauce = "+".join(subreddits)
        self.config["subreddits"] = sauce

        await self.refresh()

    async def refresh(self):
        logger.info(f"{self.name} - Refreshing submissions cache")
        self.posts = await self.reddit.hot(self.config["subreddits"])
        logger.debug(f"{self.name} - Refreshing complete")

    async def random_post(self):
        if len(self.posts) == 0:
            await self.refresh()

        return self.posts.pop(randint(0, len(self.posts) - 1))

    async def check_whitelist(self, ctx: Context):
        if not self.config["whitelist"]:
            return True
        elif ctx.channel.id not in self.config["whitelist"]:
            await ctx.message.delete()
            return False
        else:
            return True

    async def get_custom_post(self, subreddits: str):
        post_list = await self.reddit.hot(subreddits, limit=5)
        return post_list[0]

    async def send_from_reddit(self, ctx: Context, subreddits: str = ""):
        try:
            if subreddits:
                post = await self.get_custom_post(subreddits)
            else:
                post = await self.random_post()
        except HTTPException:
            await ctx.reply("There is a problem with Reddit API. Try again later", mention_author=False)
        except Forbidden:
            await ctx.reply("One or all subreddits cannot be accessed", mention_author=False)
        else:
            await ctx.reply(embed=self.create_embed(post), mention_author=False)

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
