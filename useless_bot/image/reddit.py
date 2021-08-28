from __future__ import annotations

import asyncio
import logging
from asyncio import AbstractEventLoop
from dataclasses import dataclass
from time import time
from typing import Optional, Union
from uuid import uuid4

import aiohttp
from aiohttp.web_exceptions import HTTPException

from useless_bot import __version__
from useless_bot.config import Config

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Post:
    link: str
    subreddit: str
    title: str
    author: str
    media: str
    is_video: bool

    @classmethod
    def from_api(cls, data: dict) -> Post:
        is_video = data["is_video"]

        if is_video:
            media: str = data["secure_media"]["reddit_video"]["fallback_url"].removesuffix("?source=fallback")
        else:
            media: str = data["url"]

        return cls(link=f"https://www.reddit.com{data['permalink']}",
                   subreddit=data["subreddit_name_prefixed"],
                   title=data["title"],
                   author=data["author"],
                   media=media,
                   is_video=data["is_video"])


class Forbidden(Exception):
    pass


class RedditLister:
    expires_in: int = 0
    last_auth_time: int = 0

    def __init__(self,
                 client_id: str,
                 client_secret: str,
                 *,
                 loop: Optional[AbstractEventLoop] = None,
                 connector: Optional[aiohttp.TCPConnector] = None,
                 useragent: str = f"python:useless-bot:{__version__} (by /u/MRvillager)",
                 ):
        """
        Initialize aiohttp session and config
        :param loop: a custom event loop
        :param useragent: a custom user agent to use
        """
        self.loop: AbstractEventLoop = asyncio.get_event_loop() if loop is None else loop
        self.config = Config(name="Reddit")

        if self.config["uuid"] is None:
            self.config["uuid"] = str(uuid4())

        self.headers = {
            "User-Agent": useragent
        }
        self._basic_auth = aiohttp.BasicAuth(client_id, client_secret)
        self._conn = aiohttp.TCPConnector(ttl_dns_cache=600, limit=100) if connector is not None else connector
        self._session = aiohttp.ClientSession(connector=self._conn, headers=self.headers, loop=self.loop)

    async def close(self):
        await self._session.close()

    async def _auth(self):
        """Authorize bot and save bearer token"""
        data = {
            "grant_type": "https://oauth.reddit.com/grants/installed_client",
            "device_id": self.config["uuid"]
        }

        async with self._session.post(url=f"https://www.reddit.com/api/v1/access_token", data=data,
                                      auth=self._basic_auth) as resp:
            resp_data = await resp.json()

        if "error" in resp_data.keys():
            logger.error(f"Error in auth: {resp_data['error']}")
            raise HTTPException

        token = resp_data["access_token"]
        self.last_auth_time = int(time())
        self.expires_in = resp_data["expires_in"] + self.last_auth_time
        self.headers["Authorization"] = f"bearer {token}"

    async def listing(self,
                      endpoint: str,
                      count: int = 0,
                      limit: int = 25,
                      g: str = "GLOBAL",
                      show: Optional[str] = None,
                      sr_detail: Optional[str] = None) -> list[Post]:
        # if the token has expired, get a new one, otherwise do nothing
        if self.expires_in <= self.last_auth_time:
            await self._auth()

        # build body for request
        data = {
            "g": g,
            "count": count,
            "limit": limit
        }

        # add to data optional arguments
        if show is not None:
            data["show"] = show
        if sr_detail is not None:
            data["sr_detail"] = sr_detail

        # make request and parse response
        async with self._session.get(url=f"https://oauth.reddit.com{endpoint}", data=data,
                                     headers=self.headers) as resp:
            listing = await resp.json()

        if "error" in listing.keys():
            logger.debug(f"Error in listing: {listing['error']}, endpoint={endpoint}")
            raise Forbidden

        # parse posts from response
        posts = []
        for post in listing["data"]["children"]:
            posts.append(Post.from_api(post["data"]))

        return posts

    async def hot(self, subreddits: Union[list[str], str], count: int = 0, limit: int = 25) -> list[Post]:
        if type(subreddits) == list:
            subreddits_str = "+".join(subreddits)
        else:
            subreddits_str = subreddits
        return await self.listing(endpoint=f"/r/{subreddits_str}/hot.json", count=count, limit=limit)
