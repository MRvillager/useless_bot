from __future__ import annotations

import asyncio
import logging
from typing import Optional

from nextcord import VoiceClient
from nextcord.ext.commands import Bot

from useless_bot.core.queue import SongQueue
from .models import VoiceEntry

__all__ = [
    "PlayerState"
]

logger = logging.getLogger("useless_bot.cogs.music.voice")


class PlayerState:
    def __init__(self, bot: Bot, voice: VoiceClient):
        self.bot = bot

        self.voice: VoiceClient = voice
        self.current: Optional[VoiceEntry] = None

        self.loop = False

        self._play_next_song = asyncio.Event()
        self._queue = SongQueue()
        self.skip_votes = set()  # a set of user_ids that voted
        self.audio_player = self.bot.loop.create_task(self.audio_player_task())

    def __del__(self):
        try:
            self.audio_player.cancel()
            del self.voice
            del self._queue
            del self.current
            del self._play_next_song
            del self.skip_votes
        except AttributeError:
            pass

    def index(self, item: VoiceEntry) -> int:
        if item == self.current:
            return 0

        i = self._queue.index(item)

        if self.is_playing():
            return i + 1
        else:
            return i

    def is_playing(self):
        return self.current is not None

    def get_queue(self) -> list:
        queue = self._queue.to_list()

        return queue

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
        del self._queue[index - 1]

    def skip(self):
        self.skip_votes.clear()

        if self.is_playing():
            self.voice.stop()

    def _play(self, error: Optional = None):
        breakpoint()
        if error is not None:
            logger.warning(error)
        elif not self._queue.is_empty or (self.loop and self.current is not None):
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

            if self.current is None or not self.loop:
                self.current = await self._queue.get()

            self.voice.play(self.current, after=self._play)

            self.bot.loop.call_soon_threadsafe(self._play_next_song.clear)
