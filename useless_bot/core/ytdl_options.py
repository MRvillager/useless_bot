import logging

from youtube_dl import utils

logger = logging.getLogger("youtube_dl")

__all__ = [
    "ytdl_format_options",
    "ffmpeg_options"
]

ytdl_format_options = {
    "format": "bestaudio",
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "noplaylist": False,
    "nocheckcertificate": True,
    "ignoreerrors": True,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",  # bind to ipv4 since ipv6 addresses cause issues sometimes
    "cachedir": "data/cache/",
    "cookiefile": "data/ytdl.cookies",
    "logger": logger,
    "default_search": "ytsearch:"
}

ffmpeg_options = {
    "options": "-vn",
    "before_options": "-reconnect 1 -reconnect_delay_max 5"
}

utils.bug_reports_message = lambda: ""
