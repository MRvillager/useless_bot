from discord.ext import commands
from discord.ext.commands import Context, Bot

from .interface import RedditCog
from .reddit import RedditLister


class Meme(RedditCog):
    """Get the "best" memes"""

    def __init__(self, discord_bot: Bot, reddit_bot: RedditLister):
        self.bot = discord_bot

        subreddits = "memes+dankmemes"
        super(Meme, self).__init__(
            reddit_bot=reddit_bot, subreddits=subreddits, discord_bot=discord_bot
        )

        self.post_cache = 10

    @commands.command(usage="[subreddits...]")
    async def meme(self, ctx: Context, *args: str):
        """Get the best memes from r/memes or r/dankmemes"""
        await self.base_command(ctx, *args)
