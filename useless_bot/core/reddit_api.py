from __future__ import annotations

import logging
from dataclasses import dataclass
from time import time
from typing import Optional, Union
from uuid import uuid4

import aiohttp
from aiohttp.web_exceptions import HTTPException
from yarl import URL

from .config import Config
from .drivers import Shelve

logger = logging.getLogger("useless_bot.core.reddit_api")

schema = {"uuid": str(uuid4())}


@dataclass(frozen=True)
class Post:
    link: str
    subreddit: str
    title: str
    author: str
    media: str
    is_video: bool
    is_nsfw: bool

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
                   is_video=data["is_video"],
                   is_nsfw=data["over_18"])


class Forbidden(Exception):
    pass


class RedditAPI:
    expires_in: int = 0
    last_auth_time: int = 0

    def __init__(self,
                 client_id: str,
                 client_secret: str,
                 *,
                 session: aiohttp.ClientSession,
                 headers: dict
                 ):
        """
        Initialize aiohttp session and config
        :param loop: a custom event loop
        :param useragent: a custom user agent to use
        """
        self.config = Config(cog="RedditAPI", driver=Shelve(), schema=schema)
        self._basic_auth = aiohttp.BasicAuth(client_id, client_secret)
        self.headers = headers
        self._session = session

    async def _auth(self):
        """Authorize bot and save bearer token"""
        logging.info("Starting authentication with RedditAPI")
        data = {
            "grant_type": "https://oauth.reddit.com/grants/installed_client",
            "device_id": await self.config.get(["uuid"])
        }

        async with self._session.post(url=URL("https://www.reddit.com/api/v1/access_token"),
                                      data=data, auth=self._basic_auth) as resp:
            resp_data = await resp.json()

        if "error" in resp_data.keys():
            logger.error(f"Failed to authenticate with RedditAPI: {resp_data} - {data}")
            raise HTTPException

        logging.info("Authentication with RedditAPI successful")

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
            logging.info("Token has expired")
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
        logging.info("Getting posts from RedditAPI")
        async with self._session.get(url=URL(f"https://oauth.reddit.com{endpoint}"), data=data,
                                     headers=self.headers) as resp:
            listing = await resp.json()

        if "error" in listing.keys():
            logger.error(f"Cannot get posts from RedditAPI: {listing}, endpoint={endpoint}")
            raise Forbidden

        logging.info("Successful retrieved posts from RedditAPI")

        # parse posts from response
        posts = []
        for post in listing["data"]["children"]:
            posts.append(Post.from_api(post["data"]))

        return posts

    async def hot(self, subreddits: Union[list[str], str], count: int = 0, limit: int = 25) -> list[Post]:
        if type(subreddits) is list:
            subreddits_str = "+".join(subreddits)
        else:
            subreddits_str = subreddits
        return await self.listing(endpoint=f"/r/{subreddits_str}/hot.json", count=count, limit=limit)

    async def link(self, link: str) -> Post:
        if self.expires_in <= self.last_auth_time:
            logging.debug("Token has expired")
            await self._auth()

        post_url = URL(link.removesuffix("/").removesuffix(".json") + ".json").with_host("oauth.reddit.com")
        logging.info("Getting post from Reddit API")
        async with self._session.get(url=post_url, headers=self.headers) as resp:
            posts = await resp.json()

        if type(posts) is dict:
            logger.error(f"Cannot get post from RedditAPI: {posts['error']}, url={post_url}")
            raise Forbidden

        logging.info("Successful retrieved post from RedditAPI")

        return Post.from_api(posts[0]["data"]["children"][0]["data"])
