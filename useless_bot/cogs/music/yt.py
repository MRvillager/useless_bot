from functools import lru_cache
from discord.ext import commands
from discord.ext.commands import Context, CommandError
from youtube_dl import extractor
from .errors import URLNotSupported

__all__ = [
    "YTLink",
    "YTLinkConverter"
]

ytdl_extractors = extractor.gen_extractor_classes()


class YTLink(str):
    pass


class YTLinkConverter(commands.Converter):
    @staticmethod
    @lru_cache(maxsize=128)
    def is_supported(url: str) -> bool:
        for ext in ytdl_extractors:
            if ext.suitable(url):
                return True

        raise URLNotSupported("URL not supported")

    async def convert(self, ctx: Context, argument: str) -> YTLink:
        # TODO: link parsing
        if self.is_supported(argument):
            return YTLink(argument)
