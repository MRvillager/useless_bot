import datetime
import logging
import nextcord

from nextcord import InviteTarget, Embed, Color, ButtonStyle
from nextcord.ext.commands import Bot, Cog, command, Context, CommandError

from useless_bot.cogs.music.errors import AuthorNotConnected
from useless_bot.utils import on_global_command_error


# Application ids source: https://gist.github.com/Bendimester23/98cdabec9dedc18a97d3d2bb68715919


__all__ = ["Activity"]


logger = logging.getLogger("useless_bot.cog.activity")


class ActivityView(nextcord.ui.View):
    def __init__(self, url: str):
        super().__init__()

        self.add_item(nextcord.ui.Button(label="Click Here", url=url, style=ButtonStyle.url))


class Activity(Cog):
    """Launch activities"""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def cog_command_error(self, ctx: Context, error: CommandError):
        if isinstance(error, AuthorNotConnected):
            await ctx.send("You are not connected to a voice channel")
        elif not await on_global_command_error(ctx, error):
            logger.error(f"Exception occurred", exc_info=True)

    @staticmethod
    async def base_activity_launcher(ctx: Context, app_id: int):
        invite = await ctx.author.voice.channel.create_invite(
            reason=f"Watch together party for {ctx.author.mention}",
            max_age=3600,
            target_type=InviteTarget.embedded_application,
            target_application_id=app_id,
            temporary=True
        )

        embed = Embed(
            colour=Color.red(),
            type="link",
            url=invite.url,
            title="Activity created!",
            description="Click the button below to start the activity",
            timestamp=datetime.datetime.now()
        )

        embed.set_author(
            name=f"{ctx.author.display_name}#{ctx.author.discriminator}",
            icon_url=ctx.author.display_avatar.url
        )

        view = ActivityView(url=invite.url)

        await ctx.send(view=view, embed=embed)

    @command()
    async def youtube(self, ctx: Context):
        """Launches watch together application"""
        await self.base_activity_launcher(ctx=ctx, app_id=755600276941176913)

    @command()
    async def chess(self, ctx: Context):
        """Launches a chess game"""
        await self.base_activity_launcher(ctx=ctx, app_id=832012774040141894)

    @command()
    async def poker(self, ctx: Context):
        """Launches a poker game"""
        await self.base_activity_launcher(ctx=ctx, app_id=755827207812677713)

    @command()
    async def fishing(self, ctx: Context):
        """Launches a fishing game"""
        await self.base_activity_launcher(ctx=ctx, app_id=814288819477020702)

    @command()
    async def betrayal(self, ctx: Context):
        """Launches a betrayal game"""
        await self.base_activity_launcher(ctx=ctx, app_id=773336526917861400)

    @youtube.before_invoke
    async def ensure_voice(self, ctx: Context):
        if not ctx.author.voice:
            raise AuthorNotConnected("Author not connected to a voice channel.")
