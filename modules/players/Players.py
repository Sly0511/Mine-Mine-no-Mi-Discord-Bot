from discord.ext import commands
from discord import app_commands, Embed
from utils.objects import PlayerData, Factions
from discord.utils import get


class Players(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.players = []

    @commands.Cog.listener("on_player_data")
    async def update_player_data(self, player_data: list[PlayerData]):
        """Updates the devil fruit circulation."""
        await self.bot.modules_ready.wait()
        self.players = player_data

    @app_commands.command(name="player", description="Get player detailed data.")
    async def get_player(self, interaction, *, player: str):
        """Gets a player's data."""
        player: PlayerData = get(self.players, uuid=player)
        embed = Embed(title=player.name)
        embed.add_field(name="Race", value=getattr(player.race, "name", "Not Selected"))
        embed.add_field(
            name="Sub Race",
            value=getattr(player.sub_race, "name", "Not Selected or N/A"),
        )
        embed.add_field(
            name="Faction", value=getattr(player.faction, "name", "Not Selected")
        )
        embed.add_field(name="Belly", value=player.belly)
        embed.add_field(
            name="Eaten Devil Fruits",
            value="\u200b"
            + "\n".join([f.format_name for f in player.eaten_devil_fruits]),
        )
        embed.add_field(
            name="Inventory Devil Fruits",
            value="\u200b"
            + "\n".join([f.format_name for f in player.inventory_devil_fruits]),
        )
        embed.add_field(name="Doriki", value=player.doriki)
        embed.add_field(
            name="Loyalty",
            value=player.loyalty if player.faction == Factions.Marine else "N/A",
        )
        embed.add_field(name="Bounty", value=player.bounty)
        embed.add_field(
            name="Haki",
            value=(
                f"Hardening: {player.harderning_haki}\n"
                + f"Imbuing: {player.imbuing_haki}\n"
                + f"Observation: {player.observation_haki}\n"
                + f"Conquerors: "
                + ("Yes" if player.haoshoku_haki else "No")
            ),
        )

        embed.set_footer(text="UUID: {}".format(player.uuid))
        await interaction.response.send_message(embed=embed)

    @get_player.autocomplete("player")
    async def get_player_autocomplete(self, ctx, current: str):
        """Autocomplete for the player command."""
        players = list(
            filter(lambda x: x.name.lower().startswith(current.lower()), self.players)
        )
        return [
            app_commands.Choice(name=player.name, value=player.uuid)
            for player in players
        ][:25]


async def setup(bot):
    await bot.add_cog(Players(bot))
