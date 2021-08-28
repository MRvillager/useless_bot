from discord.ext.commands import Context


async def is_admin(ctx: Context):
    # Check if user is admin
    return ctx.author.guild_permissions.administrator
