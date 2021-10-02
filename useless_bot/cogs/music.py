import asyncio
import re
import logging

from asyncio import sleep
from typing import Union
from discord import Embed, VoiceClient
from discord.ext import commands
from discord.ext.commands import Bot, is_nsfw, Context, CommandError, bot_has_permissions
from discord.types import snowflake

from useless_bot.core.ytdl import YTDL, NotFound, QueueEnd
from useless_bot.utils import on_global_command_error

logger = logging.getLogger("useless_bot.cog.music")


class YTLink(commands.Converter, str):
    yt_re = re.compile(r"^.*(youtu.be/|list=)([^#&?]*).*")

    async def convert(self, _: Context, argument: str) -> "YTLink":
        argument = argument.lower()

        if re.match(self.yt_re, argument):
            return YTLink(argument)
        else:
            raise TypeError


class Music(commands.Cog):
    # todo: dj role
    # todo: custom volume
    def __init__(self, discord_bot: Bot):
        self.guild_ytdl: dict[snowflake, YTDL] = {}
        self.bot = discord_bot

    async def cog_command_error(self, ctx: Context, error: CommandError) -> None:
        if isinstance(error, NotFound):
            await ctx.send("Nothing found")
        elif isinstance(error, asyncio.exceptions.TimeoutError):
            pass
        #elif not await on_global_command_error(ctx, error):
        else:
            logger.error(f"Exception occurred", exc_info=True)

    async def cog_check(self, ctx: Context):
        if ctx.guild:
            if ctx.voice_client is None:
                if ctx.author.voice:
                    ctx.bot.loop.create_task(ctx.author.voice.channel.connect(timeout=60))
                    return True
                else:
                    await ctx.send("You are not connected to a voice channel.")
                    return False
        return False

    def get_guild_ytdl(self, ctx: Context) -> YTDL:
        if not self.guild_ytdl.get(ctx.guild.id):
            self.guild_ytdl[ctx.guild.id] = YTDL(channel=ctx.channel)
        return self.guild_ytdl[ctx.guild.id]

    # noinspection PyTypeChecker
    async def _play(self, ctx: Context):
        voice_client: VoiceClient = ctx.voice_client
        ytdl = self.guild_ytdl[ctx.guild.id]

        # player loop
        while True:
            # check if is still connected to the channel
            if not voice_client.is_connected():
                break

            # try to get a song from the queue
            try:
                song = ytdl.pop()
            except QueueEnd:
                # try again after 30 seconds
                await sleep(30)

                try:
                    # noinspection PyUnusedLocal
                    song = ytdl.pop()
                except QueueEnd:
                    break

            else:
                voice_client.play(song, after=lambda e: logger.error(f"Player error: {e}") if e else None)

    # noinspection PyTypeChecker
    @commands.command(aliases=["p"])
    async def play(self, ctx: Context, *, query: Union[YTLink, str]):
        """Add to queue a song or a playlist"""
        ytdl = self.get_guild_ytdl(ctx)

        if type(query) is YTLink:
            await ytdl.add_url_to_queue(YTLink)
        else:
            song = await ytdl.search(YTLink).__anext__()
            ytdl.add_to_queue(song)

        ctx.bot.loop.create_task(self._play(ctx))

    # noinspection PyTypeChecker
    @commands.command(aliases=["pn"])
    async def playnow(self, ctx: Context, query: Union[YTLink, str]):
        """Play now a song"""
        ytdl = self.get_guild_ytdl(ctx)

        if type(query) is YTLink:
            await ytdl.add_url_first_to_queue(YTLink)
        else:
            song = await anext(ytdl.search(YTLink))
            ytdl.add_to_queue(song, index=0)

        ctx.bot.loop.create_task(self._play(ctx))

    @commands.command(aliases=["r"])
    async def remove(self, ctx: Context, num: int):
        """Remove a song from the queue"""
        ytdl = self.get_guild_ytdl(ctx)

        try:
            ytdl.remove(num)
        except IndexError:
            await ctx.send("There is nothing a that index")

    @commands.command(aliases=["fs"])
    async def forceskip(self, ctx: Context):
        """Skip a song"""
        # noinspection PyUnresolvedReferences
        ctx.voice_client.stop()

        await ctx.send("Skipped")

    @commands.command()
    async def loop(self, ctx: Context):
        """Loop over the current song"""
        ytdl = self.get_guild_ytdl(ctx)

        ytdl.loop = not ytdl.loop

        if ytdl.loop:
            await ctx.send("Loop enabled")
        else:
            await ctx.send("Loop disabled")

    @commands.command()
    async def loopqueue(self, ctx: Context):
        """Loop over the queue"""
        ytdl = self.get_guild_ytdl(ctx)

        ytdl.loopqueue = not ytdl.loopqueue

        if ytdl.loopqueue:
            await ctx.send("Loopqueue enabled")
        else:
            await ctx.send("Loopqueue disabled")

    @commands.command()
    async def bassboost(self, ctx: Context):
        """Bass boost the current song"""
        raise NotImplemented

    @commands.command(aliases=["quit"])
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""
        await ctx.voice_client.disconnect()
