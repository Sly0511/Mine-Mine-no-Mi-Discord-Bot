from discord import app_commands, Embed
from discord.ext import commands
from utils.checks import is_bot_owner_interaction
from mcrcon import MCRcon


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

    @app_commands.command(name="staff", description="List all staff members.")
    async def staff_list(self, interaction):
        staff_role = interaction.guild.get_role(self.bot.config.staff_role)
        staff = staff_role.members
        staff.sort(key=lambda x: -x.roles[-1].position)
        embed = Embed(title=self.bot.config.server_name + " Staff", description="")
        for role in reversed(interaction.guild.roles):
            if role.position > staff_role.position:
                if not role.members or role.id == 1011148747599790082:
                    continue
                members = "\n".join([m.mention for m in sorted(role.members, key=lambda x: -x.roles[-1].position)])
                embed.add_field(name=role.name, value=members)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="rcon", description="Run a console command.")
    @is_bot_owner_interaction()
    async def rcon(self, interaction, command: str):
        with MCRcon(
            host=self.bot.config.server_ip, password=self.bot.config.rcon_password, port=self.bot.config.rcon_port
        ) as rcon:
            response = rcon.command(f"/{command}")
            await interaction.response.send_message(response or "Command ran successfully")


async def setup(bot):
    await bot.add_cog(General(bot))
