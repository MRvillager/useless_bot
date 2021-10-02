from youtube_dl import utils

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
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",  # bind to ipv4 since ipv6 addresses cause issues sometimes
    "cachedir": "data/cache/",
    "cookiefile": "data/ytdl.cookies"
}

ffmpeg_options = {
    "options": "-vn"
}

utils.bug_reports_message = lambda: ""
