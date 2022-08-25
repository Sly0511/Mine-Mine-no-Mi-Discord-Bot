from discord.ext import commands
from discord import app_commands


def is_bot_owner():
    """Check if the user is a bot owner"""

    def predicate(ctx) -> bool:
        if ctx.author.id in ctx.bot.config.bot_owners:
            return True
        return False

    return commands.check(predicate)


def is_bot_owner_interaction():
    """Check if the user is a bot owner"""

    def predicate(interaction) -> bool:
        if interaction.user.id in interaction.client.config.bot_owners:
            return True
        return False

    return app_commands.check(predicate)


def is_bot_admin():
    """Check if the user is a bot owner"""

    def predicate(ctx) -> bool:
        if ctx.author.id in ctx.bot.config.bot_owners + ctx.bot.config.bot_admins:
            return True
        return False

    return commands.check(predicate)


def is_bot_admin_interaction():
    """Check if the user is a bot owner"""

    def predicate(interaction) -> bool:
        if interaction.user.id in interaction.client.config.bot_owners + interaction.client.config.bot_admins:
            return True
        return False

    return app_commands.check(predicate)
