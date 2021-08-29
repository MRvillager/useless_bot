import logging
from asyncio import get_event_loop
from os import getenv

import aiohttp
from discord import Status, Game, Intents
from discord.ext import commands
from discord.ext.commands import check
from pretty_help import PrettyHelp

from .arcade import arcade
from .image import sauce, meme
from .image.reddit import RedditLister
from .management import management, settings
from .money import interface, bank
from .roles import roles

logger = logging.getLogger(__name__)


class UselessBot(commands.Bot):
    def __init__(self, debug: bool = False):
        self.loop = get_event_loop()
        conn = aiohttp.TCPConnector(ttl_dns_cache=600, limit=100, loop=self.loop)

        super().__init__(command_prefix=commands.when_mentioned_or('-'),
                         description="a useless bot",
                         case_insensitive=True,
                         intents=Intents(guilds=True, guild_messages=True, reactions=True, members=True,
                                         presences=True),
                         connector=conn,
                         loop=self.loop,
                         help_command=PrettyHelp())

        self.debug = debug
        self.bank = bank.Bank()

        client_id = getenv("REDDIT_ID")
        client_secret = getenv("REDDIT_SECRET")
        self.reddit_bot = RedditLister(client_id=client_id, client_secret=client_secret,
                                       connector=conn, loop=self.loop)

        self.add_cog(meme.Meme(discord_bot=self, reddit_bot=self.reddit_bot))
        self.add_cog(sauce.Sauce(discord_bot=self, reddit_bot=self.reddit_bot, bank=self.bank, connector=conn))
        self.add_cog(settings.Settings(self))
        self.add_cog(management.Management(self))
        self.add_cog(roles.Roles(self, bank=self.bank))
        self.add_cog(interface.BankInterface(self, bank=self.bank))
        self.add_cog(arcade.Arcade(self, bank=self.bank))

    # Log the start of bot
    async def on_ready(self):
        logger.info(f"Logged in as {self.user} ({self.user.id})")

        if self.debug:
            await self.change_presence(status=Status.do_not_disturb, activity=Game(name="Testing new release"))
        else:
            await self.change_presence(activity=Game(name="Overwatch 2"))

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
