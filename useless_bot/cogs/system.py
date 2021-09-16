import logging

from platform import uname, python_compiler, python_implementation, python_version
from discord import Embed
from discord.ext import commands
from discord.ext.commands import Bot, Context, is_owner, CommandError, check

from useless_bot.utils import is_admin

logger = logging.getLogger(__name__)


class System(commands.Cog):
    """Get bot and system infos"""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def cog_command_error(self, ctx: Context, error: CommandError):
        if isinstance(error, commands.BadArgument):
            await ctx.send(
                "Passed arguments are not correct",
                mention_author=False,
            )
        else:
            await ctx.send("An error happened. Retry later")
            logger.error(f"Error in Management: {error}")

    @is_owner()
    @commands.command(hidden=True)
    async def shutdown(self, _: Context):
        """Shutdown the bot"""
        await self.bot.close()

    @check(is_admin)
    @commands.command()
    async def print(self, ctx: Context):
        """Print the raw content of a message"""
        await ctx.send(f"`{ctx.message.content}`")

    @commands.command()
    async def system(self, ctx: Context):
        """Print information about the host"""
        embed = Embed()
        embed.title = "System Infos"
        sysinfo = uname()

        embed.add_field(name="Machine Name", value=sysinfo.node)
        embed.add_field(name="Processor", value=sysinfo.processor)
        embed.add_field(name="Operating System", value=f"{sysinfo.system} {sysinfo.version}")
        await ctx.send(embed=embed)

    @commands.command()
    async def python(self, ctx: Context):
        """Print information about the python interpreter"""
        embed = Embed()
        embed.title = "Python Infos"

        embed.add_field(name="Version", value=python_version())
        embed.add_field(name="Implementation", value=python_implementation())
        embed.add_field(name="Compiled using", value=python_compiler())
        await ctx.send(embed=embed)

    @commands.command()
    async def debug(self, ctx: Context):
        """Print various infos"""
        embed = Embed()
        embed.title = "Various Infos"

        embed.add_field(name="Guild ID", value=f"{ctx.guild.id}")
        embed.add_field(name="Channel ID", value=f"{ctx.channel.id}")
        embed.add_field(name="Your ID", value=f"{ctx.author.id}")
        await ctx.send(embed=embed)
