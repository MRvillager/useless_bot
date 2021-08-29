import logging

from discord.ext import commands
from discord.ext.commands import group, Bot, Context, CommandError

logger = logging.getLogger(__name__)


class Settings(commands.Cog, name="Settings Menu"):
    """Edit bot settings"""

    def __init__(self, bot: Bot):
        self.bot = bot

        self.meme = self.bot.get_cog("Meme")
        self.roles = self.bot.get_cog("Roles")
        self.sauce = self.bot.get_cog("Sauce")

    async def cog_check(self, ctx: Context):
        # Check if user is admin
        return ctx.author.guild_permissions.administrator

    async def cog_command_error(self, ctx: Context, error: CommandError):
        if isinstance(error, commands.BadArgument):
            await ctx.reply(
                "Passed arguments are not correct",
                mention_author=False,
            )
        else:
            await ctx.reply("An error happened. Retry later", mention_author=False)
            logger.error(f"Error in Settings: {error}")

    @group(invoke_without_command=True, hidden=True)
    async def settings(self, ctx: Context):
        """Handles global bot configuration"""

    @settings.group(invoke_without_command=True)
    async def roles(self, ctx: Context):
        """Handles roles configuration"""

    @settings.group(invoke_without_command=True)
    async def sauce(self, ctx: Context):
        """Handles sauce configuration"""

    @settings.group(invoke_without_command=True)
    async def meme(self, ctx: Context):
        """Handles meme configuration"""

    @roles.command()
    async def price(self, ctx: Context, price: int):
        if price >= 0:
            self.roles.config["price"] = price
            await ctx.reply(
                "Price set",
                mention_author=False,
            )
        else:
            await ctx.reply(
                "The price must be a positive integer",
                mention_author=False,
            )

    @meme.command(aliases=["subreddits"], usage="<subreddits...>", name="default")
    async def m_default(self, ctx: Context, *args):
        """Get or edit the current default subreddits for memes"""
        if args:
            await self.meme.source("+".join(list(args)))
        await ctx.reply(
            f"Default subreddits: r/{' r/'.join(self.meme.config['subreddits'].split('+'))}",
            mention_author=False,
        )

    @meme.command(usage="<channels...>", name="whitelist")
    async def m_whitelist(self, ctx: Context, *args):
        """Get or edit the current channel whitelist for memes"""
        if args:
            channels = [int(x.removeprefix("<#").removesuffix(">")) for x in args]
            whitelist = args
            self.meme.config["whitelist"] = channels
        else:
            whitelist = [f"<#{x}>" for x in self.meme.config["whitelist"]]

        await ctx.reply(
            f"Current whitelist: {' '.join(whitelist)}", mention_author=False
        )

    @sauce.command(aliases=["subreddits"], usage="<subreddits...>", name="default")
    async def s_default(self, ctx: Context, *args):
        """Get or edit the current default subreddits for sauce"""
        if len(args) != 0:
            await self.sauce.source(args)
        await ctx.reply(
            f"Default subreddits: r/{' r/'.join(self.sauce.config['subreddits'].split('+'))}",
            mention_author=False,
        )

    @sauce.command(usage="<channels...>", name="whitelist")
    async def s_whitelist(self, ctx: Context, *args):
        """Get or edit the current channel whitelist for sauce"""
        if args:
            channels = [int(x.removeprefix("<#").removesuffix(">")) for x in args]
            self.sauce.config["whitelist"] = channels
            whitelist = args
        else:
            whitelist = [f"<#{x}>" for x in self.sauce.config["whitelist"]]

        await ctx.reply(
            f"Current whitelist: {' '.join(whitelist)}", mention_author=False
        )
