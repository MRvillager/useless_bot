import logging
from typing import Union

import lavalink
import yarl
from lavalink import Player, Track
from lavalink.rest_api import LoadResult
from nextcord import Embed, Color
from nextcord.ext import commands
from nextcord.ext.commands import Context, CommandError, Bot

from useless_bot.utils import on_global_command_error, parse_seconds
from .errors import *
from .models import URLConverter

__all__ = ["Music"]

logger = logging.getLogger("useless_bot.cogs.music.music")


class Music(commands.Cog):
    def __init__(self, discord_bot: Bot):
        self.bot = discord_bot

    async def cog_command_error(self, ctx: Context, error: CommandError) -> None:
        if isinstance(error, AuthorNotConnected):
            await ctx.send("❌ You are not connected to a voice channel")
        elif isinstance(error, NotFound):
            await ctx.send("❌ Cannot play this URL")
        elif isinstance(error, URLNotSupported):
            await ctx.send("❌ This URL is not supported")
        elif isinstance(error, PlaylistIsEmpty):
            await ctx.send("❌ This Playlist is empty")
        elif isinstance(error, VoiceNotTheSame):
            await ctx.send("❌ I'm already in a channel. You must connect to it to give me orders")
        elif isinstance(error, KeyError) or isinstance(error, IndexError):
            await ctx.send("❌ Parsing error")
            logger.error(f"Parsing error occurred", exc_info=True)
        elif not await on_global_command_error(ctx, error):
            logger.error(f"Exception occurred", exc_info=True)

    @staticmethod
    async def _get_player(ctx: Context) -> Player:
        try:
            player = lavalink.get_player(ctx.guild.id)
        except KeyError:
            player = await lavalink.connect(ctx.author.voice.channel, True)

        return player

    @staticmethod
    async def playlist_embed(result: LoadResult) -> Embed:
        embed = Embed(color=Color.random(), type="link")

        embed.title = result.playlist_info.name
        embed.set_thumbnail(url=result.tracks[0].thumbnail)

        embed.add_field(name="Enqueued", value=len(result.tracks))

        return embed

    @staticmethod
    async def song_embed(result: Track) -> Embed:
        embed = Embed(color=Color.random(), type="link")

        embed.title = result.title
        embed.set_author(name=result.author)
        embed.set_thumbnail(url=result.thumbnail)

        embed.add_field(name="Video duration", value=parse_seconds(result.length // 1000))

        return embed

    @commands.command(aliases=["p", "pp"])
    async def play(self, ctx: Context, *, query: Union[URLConverter, str]):
        """Play a song"""
        embed: Embed
        player = await self._get_player(ctx)

        if isinstance(query, yarl.URL):
            # noinspection PyTypeChecker
            tracks = await player.load_tracks(query)
        else:
            tracks = await player.search_yt(query)

        if tracks.is_playlist:
            embed = await self.playlist_embed(tracks)
            for track in tracks.tracks:
                player.add(ctx.author, track)
        else:
            embed = await self.song_embed(tracks.tracks[0])
            player.add(ctx.author, tracks.tracks[0])

        # send feedback to user
        await ctx.send(embed=embed)

        # play music
        if not player.current:
            await ctx.send("▶ Now playing")
            await player.play()

    @commands.command(aliases=["repeat"])
    async def loop(self, ctx: Context):
        """Toggle repeat"""
        player = await self._get_player(ctx)
        player.repeat = not player.repeat

        if player.repeat:
            await ctx.send("🔂 Loop on")
        else:
            await ctx.send("➡ Loop off")

    @commands.command()
    async def stop(self, ctx: Context):
        """Stop and clear queue"""
        player = await self._get_player(ctx)
        await player.stop()
        await ctx.send("⏹ Stopped music")

    @commands.command(aliases=["s"])
    async def skip(self, ctx: Context):
        """Skip current song"""
        player = await self._get_player(ctx)
        await player.skip()
        await ctx.send("⏩ Skipped")

    @commands.command()
    async def pause(self, ctx: Context):
        """Pause current song"""
        player = await self._get_player(ctx)
        await player.pause()
        await ctx.send("⏸ Paused")

    @commands.command()
    async def resume(self, ctx: Context):
        """Resume current song"""
        player = await self._get_player(ctx)
        await player.pause(pause=True)
        await ctx.send("⏯ Now playing")

    @commands.command(aliases=["fuckoff"])
    async def quit(self, ctx: Context):
        """Disconnect bot from channel"""
        player = await self._get_player(ctx)
        await player.disconnect()
        await ctx.send("⭕ Successfully disconnected")

    @commands.command(aliases=["shufflequeue"])
    async def shuffle(self, ctx: Context):
        """Disconnect bot from channel"""
        player = await self._get_player(ctx)
        await player.force_shuffle()
        await ctx.send("🔀 Queue shuffled")

    @commands.command()
    async def loopqueue(self, ctx: Context):
        """Disconnect bot from channel"""
        player = await self._get_player(ctx)

        player.loopqueue = not player.loopqueue

        if player.loopqueue:
            await ctx.send("🔁 Loopqueue on")
        else:
            await ctx.send("➡ Loopqueue off")

    @commands.command(aliases=["nightcore"])
    async def timescale(self, ctx: Context, speed: float = 1.2, pitch: float = 1.1, rate: float = 1.2):
        """Disconnect bot from channel"""
        player = await self._get_player(ctx)
        await player.timescale(speed, pitch, rate)
        await ctx.send("🆒 Timescaled successful")

    @commands.command()
    async def bassboost(self, ctx: Context):
        player = await self._get_player(ctx)
        await player.bass_boost()
        await ctx.send("🅱 Bass boost enabled")

    @commands.command()
    async def karaoke(self, ctx: Context):
        player = await self._get_player(ctx)
        await player.karaoke()
        await ctx.send("🎤 Karaoke enabled")

    @commands.command()
    async def distortion(self, ctx: Context):
        player = await self._get_player(ctx)
        await player.random_distortion()
        await ctx.send("🔣 Random distortion on")

    @commands.command()
    async def rotation(self, ctx: Context):
        player = await self._get_player(ctx)
        await player.rotation()
        await ctx.send("🌀 Rotation on")
