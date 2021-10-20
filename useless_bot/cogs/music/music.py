import asyncio
import logging
from typing import Union

import nextcord
import youtube_dl
from nextcord import Embed, Color, Member, VoiceState
from nextcord.ext import commands
from nextcord.ext.commands import Context, has_permissions, CommandError, Bot

from useless_bot.core.ytdl_options import ytdl_format_options, ffmpeg_options
from useless_bot.utils import on_global_command_error, parse_seconds
from .errors import *
from .models import VoiceData, VoiceEntry, YTLink, YTLinkConverter, Playlist
from .voice import PlayerState

__all__ = [
    "Music"
]

logger = logging.getLogger("useless_bot.cogs.music.music")


class Music(commands.Cog):
    ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

    def __init__(self, discord_bot: Bot):
        self.bot = discord_bot
        self.voice_states: dict[int, PlayerState] = {}

    async def cog_command_error(self, ctx: Context, error: CommandError) -> None:
        if isinstance(error, AuthorNotConnected):
            await ctx.send("You are not connected to a voice channel")
        elif isinstance(error, NotFound):
            await ctx.send("Cannot play this URL")
        elif isinstance(error, URLNotSupported):
            await ctx.send("This URL is not supported")
        elif isinstance(error, PlaylistIsEmpty):
            await ctx.send("This Playlist is empty")
        elif isinstance(error, VoiceNotTheSame):
            await ctx.send("I'm already in a channel. You must connect to it to give me orders")
        elif isinstance(error, KeyError) or isinstance(error, IndexError):
            await ctx.send("Parsing error")
            logger.error(f"Parsing error occurred", exc_info=True)
        elif not await on_global_command_error(ctx, error):
            logger.error(f"Exception occurred", exc_info=True)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
        if member == self.bot.user:
            if after.channel is None:
                try:
                    voice_state = self.voice_states.pop(member.guild.id)
                except KeyError:
                    pass
                else:
                    del voice_state
        elif before.channel is not None:
            if before.channel.guild.id in self.voice_states:
                if len(before.channel.members) == 1:
                    if after.channel is not None:
                        await member.guild.voice_client.move_to(after.channel)
                    elif before.channel.members[0] == self.bot.user and after.channel:
                        await member.guild.voice_client.disconnect(force=False)

    def get_voice(self, ctx: Context) -> PlayerState:
        voice = self.voice_states.get(ctx.guild.id)

        if voice is None:
            # noinspection PyTypeChecker
            voice = PlayerState(bot=self.bot, voice=ctx.voice_client)
            self.voice_states[ctx.guild.id] = voice

        return voice

    @staticmethod
    async def playlist_embed(voice: PlayerState, result: Playlist) -> Embed:
        embed = Embed(color=Color.random(), type="link")

        embed.url = result.webpage_url
        embed.title = result.title
        embed.description = f"Playlist requested by {result.requester.display_name}"
        embed.set_author(name=result.uploader, url=result.uploader_url)
        embed.set_thumbnail(url=result.thumbnail)

        embed.add_field(name="Position in queue", value=voice.index(result[0]))
        embed.add_field(name="Playlist duration", value=parse_seconds(result.duration))
        embed.add_field(name="Enqueued", value=len(result))

        return embed

    @staticmethod
    async def song_embed(voice: PlayerState, result: VoiceEntry) -> Embed:
        embed = Embed(color=Color.random(), type="link")
        data = result.data

        embed.url = data.webpage_url
        embed.title = data.title
        embed.set_author(name=data.uploader, url=data.uploader_url)
        embed.set_thumbnail(url=data.thumbnail)

        embed.add_field(name="Position in queue", value=voice.index(result))
        if not data.is_live:
            embed.description = f"Song requested by {result.requester.display_name}"
            embed.add_field(name="Song duration", value=parse_seconds(data.duration))
        else:
            embed.description = f"Live requested by {result.requester.display_name}"

        return embed

    @commands.command(aliases=["p", "pp"])
    async def play(self, ctx: Context, *, query: Union[YTLinkConverter, str]):
        """Play a song"""
        embed: Embed
        voice = self.get_voice(ctx)

        if isinstance(query, YTLink):  # if it's a supported link
            try:
                result = await self.from_url(url=query, author=ctx.author)
            except NotFound:
                await ctx.send("Cannot play this URL")
                return

            if isinstance(result, Playlist):
                # add songs to queue
                await voice.add_to_queue(*result)
                # create feedback for user
                embed = await self.playlist_embed(voice, result)
            else:
                # add song to queue
                await voice.add_to_queue(result)
                # create feedback for user
                embed = await self.song_embed(voice, result)
        else:  # if it's not a supported link or it's a query
            # search query and get the first entry
            result = await self._search_single(query=query, author=ctx.author)

            # add song to queue
            await voice.add_to_queue(result)

            # create feedback for user
            embed = await self.song_embed(voice, result)

        # start playing
        voice.play()

        # send feedback to user
        await ctx.send(embed=embed)

    @commands.command(aliases=["repeat"])
    async def loop(self, ctx: Context):
        """Toggle repeat"""
        voice = self.voice_states.get(ctx.guild.id)

        voice.loop = not voice.loop

        if voice.loop:
            await ctx.send("Enabled song loop")
        else:
            await ctx.send("Disabled song loop")

    @commands.command()
    async def loopqueue(self, ctx: Context):
        """Toggle loopqueue"""
        voice = self.voice_states.get(ctx.guild.id)

        voice.loopqueue = not voice.loopqueue

        if voice.loopqueue:
            await ctx.send("Enabled loop queue")
        else:
            await ctx.send("Disabled loop queue")

    @commands.command(aliases=["s"])
    async def skip(self, ctx: Context):
        """Vote for skipping a song"""
        author = ctx.author
        voice_state = self.get_voice(ctx)

        if author in voice_state.voice.channel.members:
            voice_state.skip_votes.add(author)

        if len(voice_state.skip_votes) > (len(voice_state.voice.channel.members) // 2):
            voice_state.skip()
            await ctx.send("Skipped")
        else:
            await ctx.send(f"{len(voice_state.skip_votes)}/{voice_state.voice.channel.member_count / 2} votes")

    @commands.command(aliases=["fuckoff"])
    @has_permissions(manage_channels=True)
    async def quit(self, ctx: Context):
        """Disconnect bot from channel"""
        # noinspection PyUnusedLocal
        await self.voice_states.get(ctx.guild.id).voice.disconnect()
        await ctx.send("Successfully disconnected")

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
                self.get_voice(ctx)
                await ctx.send(f"Now connected to {ctx.author.voice.channel.mention}")
            else:
                raise AuthorNotConnected("Author not connected to a voice channel.")
        elif ctx.author.voice.channel != ctx.voice_client.channel and not self.bot.is_owner(ctx.author):
            raise VoiceNotTheSame("Author not connected to the same voice channel")

    @commands.command()
    async def connect(self, ctx: Context):
        await self._connect(ctx)

    @skip.before_invoke
    @forceskip.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.uploader.voice:
                return True
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.author.voice.channel != ctx.voice_client.channel and not self.bot.is_owner(ctx.author):
            raise VoiceNotTheSame("Author not connected to the same voice channel")

    async def _get_results(self, query: str) -> dict:
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None,
            lambda: self.ytdl.extract_info(f"ytsearch:{query}", download=False, ie_key='YoutubeSearch'))

        if not data.get("entries"):
            raise NotFound

        return data

    async def _search_multiple(self, author: Member, query: str) -> list[VoiceEntry]:
        data = await self._get_results(query)

        songs = []
        for raw_song in data["entries"]:
            song_data = VoiceData.from_data(raw_song)
            source = nextcord.FFmpegPCMAudio(song_data.url, **ffmpeg_options)
            song = VoiceEntry(source=source, data=song_data, author=author)

            songs.append(song)

        return songs

    async def _search_single(self, author: Member, query: str) -> VoiceEntry:
        data = await self._get_results(query)

        return VoiceEntry.from_data(data=data["entries"][0], author=author)

    async def from_url(self, author: Member, url: YTLink) -> Union[VoiceEntry, Playlist]:
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(url, download=False))

        if data is None:
            raise NotFound

        if data.get("url") is not None:
            return VoiceEntry.from_data(data=data, author=author)
        elif data["_type"] == "playlist":
            return Playlist.from_data(data=data, author=author)
        else:
            raise NotFound
