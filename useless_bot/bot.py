import logging
from asyncio import get_event_loop
from os import getenv
from typing import Any

import aiohttp
from discord import Status, Game, Intents
from discord.ext import commands
from discord.ext.commands import check, errors, Context

from . import __version__, __author__, __title__
from .cogs import system, settings, roles, reddit, doujin, bank, general, arcade, music
from .core import bank_core, reddit_api

logger = logging.getLogger("useless_bot.bot")
useragent = f"python:{__title__}:{__version__} (by {__author__})"


class UselessBot(commands.Bot):
    def __init__(self, debug: bool = False):
        # init aiohttp
        headers = {
            "User-Agent": useragent
        }
        self.loop = get_event_loop()
        self._conn = aiohttp.TCPConnector(ttl_dns_cache=6817, limit=100, loop=self.loop)
        self._session = aiohttp.ClientSession(connector=self._conn, headers=headers, loop=self.loop,
                                              connector_owner=False)

        # super call bot class
        super().__init__(command_prefix=commands.when_mentioned_or("-"),
                         description="a useless bot",
                         case_insensitive=True,
                         intents=Intents(guilds=True, guild_messages=True, reactions=True, members=True,
                                         voice_states=True),
                         connector=self._conn,
                         loop=self.loop)

        # set class variables
        self.debug = debug

        # init bank
        self.bank = bank_core.BankCore()

        # init reddit api
        client_id = getenv("REDDIT_ID")
        client_secret = getenv("REDDIT_SECRET")
        self.reddit_bot = reddit_api.RedditAPI(client_id=client_id, client_secret=client_secret,
                                               session=self._session, headers=headers)

        # add cogs
        self.add_cog(doujin.Doujin(discord_bot=self, session=self._session))
        self.add_cog(reddit.Reddit(discord_bot=self, reddit_api=self.reddit_bot))
        self.add_cog(roles.Roles(self, bank=self.bank))
        self.add_cog(bank.Bank(self, bank=self.bank))
        self.add_cog(arcade.Arcade(self, bank=self.bank))
        self.add_cog(general.General(self))
        self.add_cog(settings.Settings(self))
        self.add_cog(system.System(self))
        self.add_cog(music.Music(self))

    async def on_ready(self):
        """Log the start of bot"""
        logger.info(f"Logged in as {self.user} ({self.user.id})")

        if self.debug:
            await self.change_presence(status=Status.do_not_disturb, activity=Game(name="Testing new release"))
        else:
            await self.change_presence(activity=Game(name="Overwatch 3"))

    @check
    async def globally_block_dms(self, ctx: commands.Context) -> bool:
        """Deny dm messages"""
        return ctx.guild is not None

    @check
    async def globally_block_message(self, ctx: commands.Context) -> bool:
        """Deny all messages except from owner when in debug mode"""
        if self.debug:
            return await self.is_owner(ctx.author)

        return True

    async def close(self):
        logger.info("Closing Bot")
        if self._closed:
            return

        self._closed = True

        for voice in self.voice_clients:
            # noinspection PyBroadException
            try:
                await voice.disconnect(force=True)
            except Exception:
                # if an error happens during disconnects, disregard it.
                pass

        if self.ws is not None and self.ws.open:
            await self.ws.close(code=1000)

        await self._session.close()
        await self.http.close()
        self._ready.clear()
        logger.info("Bot closed")

    async def on_error(self, event_method: str, *args: Any, **kwargs: Any):
        logging.error(f"Ignoring exception in {event_method}", exc_info=True)

    async def on_command_error(self, context: Context, exception: errors.CommandError):
        if self.extra_events.get("on_command_error", None):
            return

        command = context.command
        if command and command.has_error_handler():
            return

        cog = context.cog
        if cog and cog.has_error_handler():
            return

        logging.error(f"Ignoring exception in command {context.command}", exc_info=True)
