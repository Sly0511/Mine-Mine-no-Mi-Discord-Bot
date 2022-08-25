from io import BytesIO

from discord import File, app_commands
from discord.ext import commands
from discord.utils import get
from utils.objects import PlayerData


class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logs = []
        self.players = []

    @commands.Cog.listener("on_player_data")
    async def update_player_data(self, player_data: list[PlayerData]):
        """Updates the devil fruit circulation."""
        await self.bot.modules_ready.wait()
        self.players = player_data

    @commands.Cog.listener("on_logs_read")
    async def on_logs_fetched(self, logs: list[dict]):
        await self.bot.modules_ready.wait()
        self.logs = logs

    @app_commands.command(name="check_logs", description="Get player detailed logs.")
    @app_commands.checks.has_role(996679867334660192)
    async def logs_command(self, interaction, player: str):
        player: PlayerData = get(self.players, uuid=player)
        if not player:
            return await interaction.response.send_message("Player not found.")
        player_logs = []
        for log in self.logs:
            if player.name in "\n".join(log["lines"]):
                player_logs.append(log)
        log_file = ""
        for log in player_logs:
            log_file += "\n" + ("#" * 15 + "\n") * 2
            log_file += "#{} Log: {} | {}\n".format(log["index"], log["name"], log["date"])
            log_file += ("#" * 15 + "\n") * 2 + "\n"
            for line in log["lines"]:
                if player.name in line:
                    log_file += line + "\n"
        await interaction.response.send_message(
            content="Here's the logs for {}:".format(player.name),
            file=File(BytesIO(log_file.encode()), filename="test.log"),
            ephemeral=True,
        )

    @logs_command.autocomplete("player")
    async def logs_command_autocomplete(self, interaction, current: str):
        """Autocomplete for the player command."""
        players = list(filter(lambda x: x.name.lower().startswith(current.lower()), self.players))
        return [app_commands.Choice(name=player.name, value=player.uuid) for player in players][:25]


async def setup(bot):
    await bot.add_cog(Logs(bot))
