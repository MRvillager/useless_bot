import logging
from logging.handlers import TimedRotatingFileHandler

from nextcord.errors import Forbidden
from nextcord.ext.commands import Context, errors

__all__ = [
    "parse_seconds",
    "is_admin",
    "set_up_logging",
    "on_global_command_error"
]

base_logger = logging.getLogger("useless_bot")


def parse_seconds(seconds: int) -> str:
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)

    result = ""

    if hours != 0:
        result += f"{hours}:"

    result += f"{minutes}:{seconds}"
    return result


async def is_admin(ctx: Context):
    # Check if user is admin
    return ctx.author.guild_permissions.administrator


def set_up_logging(debug: bool = False):
    # Get loggers
    root_logger = logging.getLogger()
    loggers: list[logging.Logger] = [
        base_logger,
        logging.getLogger("nextcord"),
        logging.getLogger('aiohttp.client'),
        logging.getLogger('youtube_dl')
    ]

    handlers: list[logging.Handler] = []

    # Set logging levels
    root_logger.setLevel(logging.DEBUG)
    root_logger.handlers.clear()

    # Create stream handler
    stdout_handler = logging.StreamHandler()
    stdout_formatter = logging.Formatter(
        "[{asctime}] [{levelname}] {name}.{funcName}: {message}", datefmt="%H:%M:%S %d-%m-%Y", style='{'
    )
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.setFormatter(stdout_formatter)
    # Add handler
    handlers.append(stdout_handler)

    if debug:
        # Create timed file handler
        file_handler = logging.handlers.TimedRotatingFileHandler("logs/useless_bot.log", when="midnight")
        file_handler.setFormatter(stdout_formatter)
        # Set logging level
        file_handler.setLevel(logging.DEBUG)
        # Add handler
        handlers.append(file_handler)

    for logger in loggers:
        # remove already set up handlers from logger
        logger.handlers.clear()

        for handler in handlers:
            # add handlers
            logger.addHandler(handler)


async def on_global_command_error(ctx: Context, error: errors.CommandError) -> bool:
    if isinstance(error, (errors.BadArgument, errors.ConversionError, errors.UserInputError)):
        try:
            await ctx.send("Passed arguments are not correct")
        except errors.BadArgument:
            pass
    elif isinstance(error, errors.PrivateMessageOnly):
        await ctx.send("You can use this command only in private chat")
    elif isinstance(error, errors.NoPrivateMessage):
        await ctx.send("You cannot use this command in private chat")
    elif isinstance(error, (errors.CommandNotFound, errors.DisabledCommand, errors.NotOwner)):
        pass
    elif isinstance(error, errors.CommandOnCooldown):
        await ctx.send(f"This command is in cooldown. Retry after {error.retry_after} seconds")
    elif isinstance(error, errors.MaxConcurrencyReached):
        await ctx.send("An error happened. Retry later")
        base_logger.critical("Max concurrency reached. You may need to scale up the bot")
    elif isinstance(error, errors.NotOwner):
        pass
    elif isinstance(error, (errors.BotMissingPermissions, errors.MissingPermissions, Forbidden)):
        try:
            await ctx.send("This command cannot be used because I lack some of the needed permissions")
        except (errors.BotMissingPermissions, errors.MissingPermissions):
            pass
    elif isinstance(error, errors.NSFWChannelRequired):
        await ctx.send("You cannot use this command in a no-NSFW channel")
    else:
        await ctx.send("An error happened. Retry later")
        return False

    return True
