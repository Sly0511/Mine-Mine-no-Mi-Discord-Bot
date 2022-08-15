from discord.ext import commands


def is_bot_owner():
    """Check if the user is a bot owner"""

    def predicate(ctx) -> bool:
        if ctx.author.id in ctx.bot.config.bot_owners:
            return True
        return False

    return commands.check(predicate)
