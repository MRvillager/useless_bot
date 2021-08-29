import logging
from platform import uname, python_compiler, python_implementation, python_version

from discord import Member, TextChannel, Embed
from discord.ext import commands
from discord.ext.commands import Bot, Context, command, is_owner, group, CommandError

from useless_bot.config import Config

logger = logging.getLogger(__name__)


class Management(commands.Cog, name="Admin Menu"):
    """Manages sensitive elements of the bot"""

    def __init__(self, bot: Bot):
        self.bot = bot

        self._config = Config("Management")
        self._config.setdefault("stalk_users", [])

        self.meme = self.bot.get_cog("Meme")
        self.sauce = self.bot.get_cog("Sauce")

    async def cog_command_error(self, ctx: Context, error: CommandError):
        if isinstance(error, commands.BadArgument):
            await ctx.reply(
                "Passed arguments are not correct",
                mention_author=False,
            )
        else:
            await ctx.reply("An error happened. Retry later", mention_author=False)
            logger.error(f"Error in Management: {error}")

    async def cog_check(self, ctx: Context):
        # Check if user is admin
        return ctx.author.guild_permissions.administrator

    @commands.Cog.listener()
    async def on_member_remove(self, member: Member):
        channel: TextChannel = member.guild.system_channel
        await channel.send(f"<@{member.id}> è scumparito. cringe bro.")

    @commands.Cog.listener()
    async def on_member_update(self, before: Member, after: Member):
        """Send a message in system channel when a stalked member is not more offline"""
        if not self._config["stalk_users"]:
            return

        if before.id not in self._config["stalk_users"]:
            return

        if before.status == after.status:
            return

        logger.info("g")
        channel: TextChannel = after.guild.system_channel
        await channel.send("## -- ## ATTENZIONE @everyone ## -- ##\n"
                           f"il soggetto <@{after.id}> è online")

        self._config["stalk_users"].remove(before.id)

    @command(hidden=True)
    async def stalk(self, ctx: Context, user: Member):
        """Shutdown the bot"""
        if user.id in self._config["stalk_users"]:
            self._config["stalk_users"].remove(user.id)
            await ctx.reply("Stalking removed", mention_author=False)
        else:
            self._config["stalk_users"].append(user.id)
            await ctx.reply("Stalking started :)", mention_author=False)

        self._config.push()

    @is_owner()
    @command(hidden=True)
    async def shutdown(self, _: Context):
        """Shutdown the bot"""
        await self.bot.close()

    @is_owner()
    @group(hidden=True)
    async def config(self, _: Context):
        """Manage config instances"""
        pass

    @is_owner()
    @config.command(hidden=True, name="save")
    async def save_config(self, ctx: Context):
        """Save config to disk"""
        self._config.push()
        await ctx.reply("Settings saved", mention_author=False)

    @is_owner()
    @config.command(hidden=True, name="load")
    async def load_config(self, ctx: Context):
        """Reload config from disk"""
        self._config.pull()
        await ctx.reply("Settings loaded", mention_author=False)

    @is_owner()
    @command(hidden=True, name="forcerefresh")
    async def force_refresh(self, ctx: Context):
        """Refresh reddit post cache"""
        await self.meme.refresh()
        await self.sauce.refresh()
        await ctx.reply(
            "Forced refresh of submissions cache complete", mention_author=False
        )

    @is_owner()
    @command(hidden=True)
    async def print(self, ctx: Context):
        """Print the raw content of a message"""
        await ctx.reply(f"`{ctx.message.content}`", mention_author=False)

    @is_owner()
    @command(hidden=True)
    async def system(self, ctx: Context):
        """Print information about the host"""
        embed = Embed()
        embed.title = "System Infos"
        sysinfo = uname()

        embed.add_field(name="Machine Name", value=sysinfo.node)
        embed.add_field(name="Processor", value=sysinfo.processor)
        embed.add_field(name="Operating System", value=f"{sysinfo.system} {sysinfo.version}")
        await ctx.reply(embed=embed, mention_author=False)

    @is_owner()
    @command(hidden=True)
    async def python(self, ctx: Context):
        """Print information about the python interpreter"""
        embed = Embed()
        embed.title = "Python Infos"

        embed.add_field(name="Version", value=python_version())
        embed.add_field(name="Implementation", value=python_implementation())
        embed.add_field(name="Compiled using", value=python_compiler())
        await ctx.reply(embed=embed, mention_author=False)
