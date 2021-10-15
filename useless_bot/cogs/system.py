import logging
from platform import uname, python_compiler, python_implementation, python_version

from nextcord import Embed
from nextcord.ext import commands
from nextcord.ext.commands import Bot, Context, is_owner, CommandError, check

from useless_bot.utils import is_admin, on_global_command_error

logger = logging.getLogger("useless_bot.cog.system")


class System(commands.Cog):
    """Get bot and system infos"""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def cog_command_error(self, ctx: Context, error: CommandError):
        if not await on_global_command_error(ctx, error):
            logger.error(f"Exception occurred", exc_info=True)

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

        embed.add_field(name="Machine Name", value=f"{sysinfo.node}", inline=False)
        if sysinfo.machine or sysinfo.processor:
            embed.add_field(name="Processor", value=f"{sysinfo.machine} {sysinfo.processor}", inline=False)
        embed.add_field(name="Operating System", value=f"{sysinfo.system} {sysinfo.version}", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def python(self, ctx: Context):
        """Print information about the python interpreter"""
        embed = Embed()
        embed.title = "Python Infos"

        embed.add_field(name="Version", value=python_version(), inline=False)
        embed.add_field(name="Implementation", value=python_implementation(), inline=False)
        embed.add_field(name="Compiled using", value=python_compiler(), inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def debug(self, ctx: Context):
        """Print various infos"""
        embed = Embed()
        embed.title = "Various Infos"

        embed.add_field(name="Guild ID", value=f"{ctx.guild.id}", inline=False)
        embed.add_field(name="Channel ID", value=f"{ctx.channel.id}", inline=False)
        embed.add_field(name="Your ID", value=f"{ctx.author.id}", inline=False)
        await ctx.send(embed=embed)

    @is_owner()
    @commands.command()
    async def evaluate(self, ctx: Context, *, code: str):
        """Evaluate an expression"""
        response = eval(code)
        await ctx.send(f"`{response}`")

    @is_owner()
    @commands.command()
    async def execute(self, ctx: Context, *, code: str):
        """Execute code"""
        exec(code)
        await ctx.send(f"Code executed")
