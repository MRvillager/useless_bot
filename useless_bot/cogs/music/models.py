from __future__ import annotations

from functools import lru_cache
from typing import Optional, Any

import nextcord
from nextcord import PCMVolumeTransformer, FFmpegPCMAudio, Member
from nextcord.ext import commands
from nextcord.ext.commands import Context
from youtube_dl import extractor

from useless_bot.core.ytdl_options import ffmpeg_options
from .errors import URLNotSupported, PlaylistIsEmpty

__all__ = [
    "VoiceEntry",
    "VoiceData",
    "YTLink",
    "YTLinkConverter",
    "Playlist"
]

VOLUME = 1

ytdl_extractors = extractor.gen_extractor_classes()


class VoiceData:
    title: str
    url: str
    webpage_url: str
    uploader: str
    thumbnail: str

    uploader_url: Optional[str] = None
    like_count: Optional[int] = None
    dislike_count: Optional[int] = None
    nsfw: Optional[bool] = None
    is_live: Optional[bool] = None
    views: Optional[int] = None
    duration: Optional[int] = None

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

    @classmethod
    def from_data(cls, data: dict, author: Member) -> VoiceEntry:
        song_data = VoiceData.from_data(data)
        source = nextcord.FFmpegPCMAudio(song_data.url, **ffmpeg_options)
        return cls(source=source, data=song_data, author=author)


class Playlist(list):
    requester: Member

    title: str
    webpage_url: str
    uploader: str
    uploader_url: str
    thumbnail: str
    duration: int = 0

    @classmethod
    def from_data(cls, data: dict, author: Member) -> Playlist:
        if not data["entries"]:
            raise PlaylistIsEmpty

        result = cls()

        # set attributes
        result.requester = author
        result.title = data["title"]
        result.webpage_url = data["webpage_url"]
        result.uploader = data["uploader"]
        result.uploader_url = data["uploader_url"]
        result.thumbnail = data["entries"][0]["thumbnail"]

        # parse data to VoiceEntries
        for raw_song in data["entries"]:
            song_data = VoiceData.from_data(raw_song)

            if song_data.duration:
                result.duration += song_data.duration

            source = nextcord.FFmpegPCMAudio(song_data.url, **ffmpeg_options)
            song = VoiceEntry(source=source, data=song_data, author=author)

            result.append(song)

        return result


class YTLink(str):
    pass


class YTLinkConverter(commands.Converter):
    @staticmethod
    @lru_cache(maxsize=128)
    def is_supported(url: str) -> bool:
        for ext in ytdl_extractors:
            if ext.suitable(url) and ext.IE_NAME != "generic":
                return True

        raise URLNotSupported("URL not supported")

    async def convert(self, ctx: Context, argument: str) -> YTLink:
        if self.is_supported(argument):
            return YTLink(argument)
