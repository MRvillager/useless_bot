from __future__ import annotations

import asyncio
import logging
import discord

from typing import Optional, Any
from discord import TextChannel, Member, PCMVolumeTransformer, Bot, VoiceClient, FFmpegPCMAudio
from discord.ext import commands

from useless_bot.core.queue import SongQueue

__all__ = [
    "VoiceData",
    "VoiceEntry",
    "VoiceState"
]

VOLUME = 0.5

logger = logging.getLogger("useless_bot.cogs.music.voice")


class VoiceData:
    title: str
    url: str
    webpage_url: str
    uploader: str
    thumbnail: str
    duration: str

    uploader_url: Optional[str]
    like_count: Optional[int]
    dislike_count: Optional[int]
    nsfw: Optional[bool]
    is_live: Optional[bool]
    views: Optional[int]
    duration: Optional[int]

    @classmethod
    def from_data(cls, data: dict[str, Any]) -> VoiceData:
        dataclass = cls()

        dataclass.title = data.get("title")
        dataclass.url = data["url"]
        dataclass.webpage_url = data.get("webpage_url")
        dataclass.uploader = data.get("uploader")
        dataclass.uploader_url = data.get("uploader_url")
        dataclass.thumbnail = data.get("thumbnail")
        dataclass.like_count = data.get("like_count")
        dataclass.dislike_count = data.get("dislike_count")
        dataclass.nsfw = data.get("age_limit")
        dataclass.is_live = data.get("is_live")
        dataclass.duration = data.get("duration")
        dataclass.views = data.get("view_count")

        return dataclass


class VoiceEntry(PCMVolumeTransformer):
    def __init__(self, source: FFmpegPCMAudio, author: Member, data: VoiceData):
        super().__init__(source, VOLUME)

        self.requester = author
        self.data = data


class VoiceState:
    def __init__(self, bot: Bot, voice: VoiceClient):
        self.bot = bot

        self.voice: VoiceClient = voice
        self.current: Optional[VoiceEntry] = None

        self._play_next_song = asyncio.Event()
        self._queue = SongQueue()
        self.skip_votes = set()  # a set of user_ids that voted
        self.audio_player = self.bot.loop.create_task(self.audio_player_task())

    def __del__(self):
        try:
            self.audio_player.cancel()
            self.bot.loop.call_soon_threadsafe(self.voice.disconnect)
            del self.voice
            del self._queue
            del self.current
            del self._play_next_song
            del self.skip_votes
        except AttributeError:
            pass

    def is_playing(self):
        return self.current is not None

    def get_queue(self) -> list:
        queue = self._queue.to_list()

        return queue

    @property
    def loop(self) -> bool:
        return self._queue.repeat

    @loop.setter
    def loop(self, value: bool):
        self._queue.repeat = value

    @property
    def loopqueue(self) -> bool:
        return self._queue.loop

    @loopqueue.setter
    def loopqueue(self, value: bool):
        self._queue.loop = value

    async def add_to_queue(self, *args: VoiceEntry):
        for song in args:
            await self._queue.put(song)

    async def remove_from_queue(self, index: int):
        del self._queue[index]

    def skip(self):
        self.skip_votes.clear()

        if self.is_playing():
            self.voice.stop()

    def _play(self, error: Optional = None):
        if error is not None:
            logger.warning(error)
        if not self._queue.is_empty:
            self.bot.loop.call_soon_threadsafe(self._play_next_song.set)
        else:
            self.current = None

    def play(self):
        if not self.is_playing():
            self._play()

    def stop(self):
        self._play_next_song.clear()

    async def audio_player_task(self):
        while True:
            await self._play_next_song.wait()

            self.current = await self._queue.get()
            self.voice.play(self.current, after=self._play)
            self._play_next_song.clear()
