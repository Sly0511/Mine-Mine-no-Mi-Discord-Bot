import traceback

from discord.ext import commands


class Handler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener("on_message")
    async def on_message(self, message):
        """Handle messages and commands."""
        if message.author.bot:
            return
        ctx = await self.bot.get_context(message)
        if ctx.valid:
            if message.guild is None:
                return await message.channel.send(
                    "This command can only be used in a server"
                )
            if message.author.id in self.bot.config.bot_owners:
                return
        await self.bot.process_commands(message)

    @commands.Cog.listener("on_command_error")
    async def on_command_error(self, ctx, error):
        """The event triggered when an error is raised while invoking a command."""
        if isinstance(error, commands.CommandNotFound):
            return

        exception_log = "Exception in command '{}' - {}\n" "".format(
            ctx.command.qualified_name, ctx.command.cog_name
        )
        exception_log += "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )
        self.bot._last_exception = exception_log
        raise error


async def setup(bot):
    await bot.add_cog(Handler(bot))
