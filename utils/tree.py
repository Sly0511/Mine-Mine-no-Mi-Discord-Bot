from discord import app_commands
from discord.app_commands.errors import CommandNotFound, MissingRole, CheckFailure


class Tree(app_commands.CommandTree):
    async def on_error(self, interaction, error):
        if isinstance(error, (MissingRole, CheckFailure)):
            await interaction.response.send_message(
                "You don't have the required permissions to use this command.", ephemeral=True
            )
        else:
            await super().on_error(interaction, error)
