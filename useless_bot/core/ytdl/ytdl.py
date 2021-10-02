import asyncio
import discord
import youtube_dl

from typing import Iterator, Optional, AsyncGenerator

from .options import ffmpeg_options, ytdl_format_options
from .queue import Queue
from .models import *


class YTDL:
    ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
    
    def __init__(self,
                 channel: discord.TextChannel,
                 *,
                 volume: float = 0.5,
                 stream: bool = True,
                 queue: Optional[Queue] = None):

        self.queue = queue or Queue()

        self.stream = stream
        self.volume = volume
        self.channel = channel

    @property
    def loop(self) -> bool:
        return self.queue.repeat

    @loop.setter
    def loop(self, value: bool) -> None:
        self.queue.repeat = value

    @property
    def loopqueue(self) -> bool:
        return self.queue.loop

    @loopqueue.setter
    def loopqueue(self, value: bool) -> None:
        self.queue.loop = value

    def pop(self, index: Optional[int] = None) -> Song:
        if index:
            song = self.queue[index]
        else:
            song = next(self.queue)

            if song is None:
                raise QueueEnd

        filename = song["url"] if self.stream else self.ytdl.prepare_filename(song)
        return Song(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=song, volume=self.volume)

    def remove(self, index: int):
        del self.queue[index]

    async def search(self, term: str, *, loop=None) -> AsyncGenerator:
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None,
            lambda: self.ytdl.extract_info(f"ytsearch:{term}", download=not self.stream, ie_key='YoutubeSearch'))

        if not data['entries']:
            raise NotFound

        for song in data['entries']:
            yield BaseSong(**song)

    def add_to_queue(self, song: BaseSong, *, index: int = -1):
        self.queue.insert(index, song)

    async def add_url_first_to_queue(self, url: str, *, loop=None):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(url, download=not self.stream))

        if not data['entries']:
            raise NotFound

        self.queue.append(BaseSong(**data['entries'][0]))

    async def add_url_to_queue(self, url: str, *, loop=None):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(url, download=not self.stream))

        if not data['entries']:
            raise NotFound

        for song in data['entries']:
            self.queue.append(BaseSong(**song))

    @classmethod
    async def from_url(cls, url, channel, *, loop=None, stream=True, volume=0.5):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: cls.ytdl.extract_info(url, download=not stream))

        queue = Queue()

        if not data['entries']:
            raise NotFound

        for song in data['entries']:
            queue.append(BaseSong(**song))

        return cls(queue=queue, stream=stream, volume=volume, channel=channel)
