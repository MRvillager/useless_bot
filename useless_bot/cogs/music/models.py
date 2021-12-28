from __future__ import annotations

from functools import lru_cache

import yarl
from nextcord.ext import commands
from nextcord.ext.commands import Context

from .errors import URLNotSupported

__all__ = [
    "URLConverter",
]

VOLUME = 1


class URLConverter(commands.Converter):
    @staticmethod
    @lru_cache(maxsize=128)
    def is_supported(url: str) -> bool:
        p_url = yarl.URL(url)

        if p_url.host.replace("www.", "") in ["youtu.be", "youtube.com", "soundcloud.com", "twitch.tv"]:
            return True
        else:
            return False

    async def convert(self, ctx: Context, argument: str) -> yarl.URL:
        if self.is_supported(argument):
            return yarl.URL(argument)
        else:
            raise URLNotSupported("URL not supported")
