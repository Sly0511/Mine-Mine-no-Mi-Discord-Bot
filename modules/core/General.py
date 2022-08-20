from discord import app_commands, Embed
from discord.ext import commands


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="mods")
    async def mods(self, interaction):
        """
        Lists all mods installed on the server.
        """
        mods = self.bot.constants.FTPServer.listdir("mods")
        embed = Embed(
            title=f"Mods in {self.bot.config.server_name} server",
            description=f"[Download Modpack]({self.bot.config.modpack_download})\nServer IP: `{self.bot.config.server_ip}`\n",
        )
        embed.description += "```\n" + "\n".join([mod for mod in mods if mod.endswith(".jar")]) + "\n```"
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(General(bot))
