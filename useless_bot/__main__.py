# global import
import logging
from os import getenv

from .bot import UselessBot

# set-up logging
logging.basicConfig(
    format="%(asctime)s - %(filename)s - %(funcName)s - %(levelname)s: %(message)s",
    level=logging.INFO,
)

# get logger
logger = logging.getLogger(__name__)

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

# initialize bot
debug = int(getenv("DEBUG", 0))
bot = UselessBot(debug=bool(debug))

if __name__ == "__main__":
    # run bot
    bot.run(getenv("DISCORD_TOKEN"))
