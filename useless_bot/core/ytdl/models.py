import discord

from .options import ffmpeg_options

__all__ = [
    "BaseSong",
    "Song",
    "NotFound",
    "QueueEnd",
]


class NotFound(Exception):
    pass


class QueueEnd(Exception):
    pass


class BaseSong:
    title: str
    webpage_url: str
    uploader: str
    uploader_url: str
    thumbnail: str
    like_count: int
    dislike_count: int
    age_limit: bool
    is_live: bool

    def __init__(self, title: str, webpage_url: str, uploader: str, uploader_url: str,
                 thumbnail: str, like_count: int, dislike_count: int, age_limit: bool, is_live: bool, **_):
        self.title = title
        self.webpage_url = webpage_url
        self.uploader = uploader
        self.uploader_url = uploader_url
        self.thumbnail = thumbnail
        self.like_count = like_count
        self.dislike_count = dislike_count
        self.age_limit = age_limit
        self.is_live = is_live

    @property
    def url(self) -> str:
        return self.webpage_url

    @property
    def is_nsfw(self) -> bool:
        return self.age_limit

    def __eq__(self, other: "BaseSong") -> bool:
        return self.url == other.url


class Song(discord.PCMVolumeTransformer, BaseSong):
    def __init__(self, source, data: dict, *, volume: float = 0.5):
        # noinspection PyTypeChecker
        discord.PCMVolumeTransformer.__init__(source, volume)
        BaseSong.__init__(**data)

    @classmethod
    def from_base_song(cls, base_song: BaseSong) -> "Song":
        return cls(discord.FFmpegPCMAudio(base_song.url, **ffmpeg_options), data=base_song.__dict__)
