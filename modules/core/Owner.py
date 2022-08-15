import os
import re
import traceback
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import get
from utils.checks import is_bot_owner
from utils.functions import get_modules


class Traceback(discord.ui.View):
    def __init__(self, ctx, exception, timeout=60):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.exception = exception

    @discord.ui.button(label="Show Traceback", style=discord.ButtonStyle.grey)
    async def show(self, interaction: discord.Interaction, button: discord.ui.Button):
        if len(self.exception) > 2000:
            await interaction.response.send_message(
                f"```py\n{self.exception[:1990]}```", ephemeral=True
            )
            await interaction.followup.send(
                f"```py\n{self.exception[1990:3980]}```", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"```py\n{self.exception}```", ephemeral=True
            )


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    @is_bot_owner()
    async def parse(self, ctx):
        """Parse a bit of code as a command."""
        code = re.findall(r"(?i)(?s)```py\n(.*?)```", ctx.message.content)
        if not code:
            return await ctx.send("No code detected.", ephemeral=True)
        code = "    " + code[0].replace("\n", "\n    ")
        code = "async def __eval_function__():\n" + code
        # Base Variables
        async def to_file(text, format="json"):
            _f = f"file.{format}"
            with open(_f, "w+") as f:
                f.write(text)
            await ctx.send(file=discord.File(_f))
            os.remove(_f)

        additional = {}
        additional["self"] = self
        additional["feu"] = self.bot.fetch_user
        additional["fem"] = ctx.channel.fetch_message
        additional["dlt"] = ctx.message.delete
        additional["now"] = datetime.utcnow()
        additional["nowts"] = int(datetime.utcnow().timestamp())
        additional["ctx"] = ctx
        additional["sd"] = ctx.send
        additional["channel"] = ctx.channel
        additional["author"] = ctx.author
        additional["guild"] = ctx.guild
        additional["to_file"] = to_file
        try:
            exec(code, {**globals(), **additional}, locals())

            await locals()["__eval_function__"]()
        except Exception as error:
            built_error = "".join(
                traceback.format_exception(type(error), error, error.__traceback__)
            )
            view = Traceback(ctx, built_error)
            await ctx.send(content="An error occured.", view=view)

    @commands.hybrid_command(
        name="exception", description="Shows the last exception.", aliases=["error"]
    )
    @is_bot_owner()
    async def last_exception(self, ctx):
        """Shows the last exception."""
        if self.bot._last_exception:
            view = Traceback(ctx, self.bot._last_exception)
            await ctx.send(content="Last error...", view=view, ephemeral=True)
            await ctx.message.add_reaction("✅")
        else:
            await ctx.reply("No error.", ephemeral=True)

    @commands.hybrid_command(name="sync", description="Sync the bot's slash commands.")
    @is_bot_owner()
    async def sync(self, ctx):
        """Sync the bot's slash commands."""
        guild = discord.Object(id=self.bot.config.discord_server_id)
        self.bot.tree.copy_global_to(guild=guild)
        await self.bot.tree.sync(guild=guild)
        await ctx.send("Slash commands were synced!")

    @app_commands.command(name="reload", description="Reload a bot's module.")
    @is_bot_owner()
    async def reload(self, interaction: discord.Interaction, module: str):
        """Reloads a module"""
        try:
            module = get(get_modules(self.bot.modules_path), name=module)
            await self.bot.reload_extension(module.spec)
            await interaction.response.send_message(
                f"Reloaded `{module.name}`", ephemeral=True
            )
        except commands.ExtensionNotLoaded:
            await interaction.response.send_message(
                f"Module is not loaded", ephemeral=True
            )
        except commands.ExtensionFailed as e:
            await interaction.response.send_message(
                f"Failed to reload `{module.name}`\n{e}", ephemeral=True
            )

    @reload.autocomplete(name="module")
    async def reload_module_autocomplete(
        self, interaction: discord.Interaction, current: str
    ):
        """Autocomplete for reload"""
        response = []
        for module in get_modules(self.bot.modules_path):
            if module.name.lower().startswith(current.lower()):
                response.append(
                    app_commands.Choice(name=module.name, value=module.name)
                )
        return response[:25]

    @app_commands.command(name="load", description="Load a bot's module.")
    @is_bot_owner()
    async def load(self, interaction: discord.Interaction, module: str):
        """Loads a module"""
        try:
            module = get(get_modules(self.bot.modules_path), name=module)
            await self.bot.load_extension(module.spec)
            await interaction.response.send_message(
                f"Loaded `{module.name}`", ephemeral=True
            )
        except commands.ExtensionAlreadyLoaded:
            await interaction.response.send_message(
                f"`{module.name}` is already loaded", ephemeral=True
            )
        except commands.ExtensionFailed as e:
            await interaction.response.send_message(
                f"Failed to reload `{module.name}`\n{e}", ephemeral=True
            )

    @load.autocomplete(name="module")
    async def load_module_autocomplete(
        self, interaction: discord.Interaction, current: str
    ):
        """Autocomplete for load"""
        response = []
        for module in get_modules(self.bot.modules_path):
            if module.name.lower().startswith(current.lower()):
                response.append(
                    app_commands.Choice(name=module.name, value=module.name)
                )
        return response[:25]

    @app_commands.command(name="unload", description="Unload a bot's module.")
    @is_bot_owner()
    async def unload(self, interaction: discord.Interaction, module: str):
        """Unloads a module"""
        try:
            module = get(get_modules(self.bot.modules_path), name=module)
            await self.bot.unload_extension(module.spec)
            await interaction.response.send_message(
                f"Unloaded `{module.name}`", ephemeral=True
            )
        except commands.ExtensionNotLoaded:
            await interaction.response.send_message(
                f"`{module.name}` is not loaded", ephemeral=True
            )

    @unload.autocomplete(name="module")
    async def unload_module_autocomplete(
        self, interaction: discord.Interaction, current: str
    ):
        """Autocomplete for unload"""
        response = []
        for module in get_modules(self.bot.modules_path):
            if module.name.lower().startswith(current.lower()):
                response.append(
                    app_commands.Choice(name=module.name, value=module.name)
                )
        return response[:25]


async def setup(bot):
    await bot.add_cog(Owner(bot))
