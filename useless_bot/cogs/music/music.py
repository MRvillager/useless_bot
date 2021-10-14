import asyncio
from typing import Union, TYPE_CHECKING

import discord
import youtube_dl
import logging

from discord import Bot, Member, TextChannel
from discord.ext import commands
from discord.ext.commands import Context, has_permissions, bot_has_permissions, CommandError

from useless_bot.core.ytdl_options import ytdl_format_options, ffmpeg_options
from useless_bot.utils import on_global_command_error
from .voice import VoiceState, VoiceEntry, VoiceData
from .errors import NotFound, AuthorNotConnected
from .yt import YTLink, YTLinkConverter

__all__ = [
    "Music"
]

logger = logging.getLogger("useless_bot.cogs.music.music")


class Music(commands.Cog):
    ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

    def __init__(self, discord_bot: Bot):
        self.bot = discord_bot
        self.voice_states: dict[int, VoiceState] = {}

    async def cog_command_error(self, ctx: Context, error: CommandError) -> None:
        if isinstance(error, AuthorNotConnected):
            pass
        elif isinstance(error, NotFound):
            await ctx.send("Cannot play this URL")
        elif not await on_global_command_error(ctx, error):
            logger.error(f"Exception occurred", exc_info=True)

    def get_voice(self, ctx: Context) -> VoiceState:
        voice = self.voice_states.get(ctx.guild.id)

        if voice is None:
            # noinspection PyTypeChecker
            voice = VoiceState(bot=self.bot, voice=ctx.voice_client)
            self.voice_states[ctx.guild.id] = voice

        return voice

    async def playlist_embed(self, ctx: Context, result: list[VoiceEntry]):
        pass

    async def song_embed(self, ctx: Context, result: VoiceEntry):
        pass

    @commands.command(aliases=["p"])
    async def play(self, ctx: Context, *, query: Union[YTLinkConverter, str]):
        voice = self.get_voice(ctx)

        if type(query) is YTLink:
            if TYPE_CHECKING:
                # cast variable type to YTLink (for IDE)
                query: YTLink

            try:
                result = await self.from_url(ctx, query)
            except NotFound:
                await ctx.send("Cannot play this URL")
                return

            # send feedback to user
            if len(result) > 1:
                await self.playlist_embed(ctx, result)
            else:
                await self.song_embed(ctx, result[0])

            await voice.add_to_queue(*result)
        else:
            # TODO: search query
            result = await self.search(query)
            await self.song_embed(ctx, result)
            await voice.add_to_queue(result)

        voice.play()

    @commands.command(aliases=["repeat"])
    async def loop(self, ctx: Context):
        voice = self.voice_states.get(ctx.guild.id)

        voice.loop = not voice.loop

        if voice.loop:
            await ctx.send("Enabled song loop")
        else:
            await ctx.send("Disabled song loop")

    @commands.command()
    async def loopqueue(self, ctx: Context):
        voice = self.voice_states.get(ctx.guild.id)

        voice.loopqueue = not voice.loopqueue

        if voice.loopqueue:
            await ctx.send("Enabled loop queue")
        else:
            await ctx.send("Disabled loop queue")

    @commands.command()
    async def search(self, ctx: Context, *, query: str):
        raise NotImplemented

    @commands.command(aliases=["s"])
    async def skip(self, ctx: Context):
        author = ctx.author
        voice_state = self.get_voice(ctx)

        if author in voice_state.voice.channel.members:
            voice_state.skip_votes.add(author)

        if len(voice_state.skip_votes) > (voice_state.voice.channel.member_count / 2):
            voice_state.skip()
            await ctx.send("Skipped")
        else:
            await ctx.send(f"{len(voice_state.skip_votes)}/{voice_state.voice.channel.member_count / 2} votes")

    @commands.command(aliases=["fuckoff"])
    @has_permissions(manage_channels=True)
    async def quit(self, ctx: Context):
        # noinspection PyUnusedLocal
        voice_state = self.voice_states.pop(ctx.guild.id)
        del voice_state

    @commands.command(aliases=["fs"])
    @has_permissions(manage_channels=True)
    async def forceskip(self, ctx: Context):
        # TODO: DJ role
        voice_state = self.get_voice(ctx)
        voice_state.skip()

        await ctx.send("Force skipped")

    @play.before_invoke
    async def _connect(self, ctx: Context):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise AuthorNotConnected("Author not connected to a voice channel.")

    @commands.command()
    @bot_has_permissions(speak=True, connect=True)
    async def connect(self, ctx: Context):
        await self._connect(ctx)

    @skip.before_invoke
    @forceskip.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                return True
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")

    async def _search_query_multiple(self, ctx: Context, query: str) -> list[VoiceData]:

    async def _search_query_single(self, ctx: Context, query: str) -> VoiceEntry:
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None,
            lambda: self.ytdl.extract_info(f"ytsearch:{query}", download=False, ie_key='YoutubeSearch'))

        if not data['entries']:
            raise NotFound

        song_data = VoiceData.from_data(data['entries'][0])
        source = discord.FFmpegPCMAudio(song_data.url, **ffmpeg_options)
        song = VoiceEntry(source=source, data=song_data, author=ctx.author)

        return song

    async def from_url(self, ctx: Context, url: YTLink) -> list[VoiceEntry]:
        # TODO
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(url, download=False))

        if data is None:
            raise NotFound

        if data.get("entries") is None:
            if data.get("url") is None:
                raise NotFound

        result = []
        if data.get("url") is not None:
            song_data = VoiceData.from_data(data)
            source = discord.FFmpegPCMAudio(song_data.url, **ffmpeg_options)
            song = VoiceEntry(source=source, data=song_data, author=ctx.author)

            result.append(song)
        else:
            for raw_song in data["entries"]:
                song_data = VoiceData.from_data(raw_song)
                source = discord.FFmpegPCMAudio(song_data.url, **ffmpeg_options)
                song = VoiceEntry(source=source, data=song_data, author=ctx.author)

                result.append(song)

        return result
