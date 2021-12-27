import logging
import platform
from os import getenv

from .bot import UselessBot
from .utils import set_up_logging

debug = bool(int(getenv("DEBUG", 0)))
set_up_logging(debug=debug)
logger = logging.getLogger("useless_bot")

logger.info("Initializing Bot")

# silence error on closing
if platform.system() == 'Windows':
    from functools import wraps
    from asyncio.proactor_events import _ProactorBasePipeTransport


    def silence_event_loop_closed(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except RuntimeError as e:
                if str(e) != 'Event loop is closed':
                    raise

        return wrapper


    _ProactorBasePipeTransport.__del__ = silence_event_loop_closed(_ProactorBasePipeTransport.__del__)

# enable uvloop if available
try:
    # noinspection PyUnresolvedReferences
    import uvloop
except ImportError:
    logger.warning("Cannot import uvloop")
else:
    import asyncio

    logger.info("Using uvloop")
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

if __name__ == "__main__":
    # initialize bot

    bot = UselessBot(debug=debug)

    logger.debug("Bot initialization complete")

    # run bot
    logger.info("Running bot")
    bot.run(getenv("DISCORD_TOKEN"))
