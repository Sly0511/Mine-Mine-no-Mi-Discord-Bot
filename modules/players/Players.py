from datetime import datetime, timedelta

import utils.database as db
from discord import Embed, app_commands
from discord.ext import commands
from discord.utils import get
from utils.objects import Factions, PlayerData


class Players(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.players = []

    @commands.Cog.listener("on_player_data")
    async def update_player_data(self, player_data: list[PlayerData]):
        """Updates the devil fruit circulation."""
        await self.bot.modules_ready.wait()
        self.players = player_data

    @app_commands.command(name="check_player", description="Get player detailed data.")
    async def get_player(self, interaction, *, player: str):
        """Gets a player's data."""
        player: PlayerData = get(self.players, uuid=player)
        embed = Embed(title=player.name)
        embed.add_field(name="Race", value=getattr(player.race, "name", "Not Selected"))
        embed.add_field(
            name="Sub Race",
            value=getattr(player.sub_race, "name", "Not Selected or N/A"),
        )
        embed.add_field(name="Faction", value=getattr(player.faction, "name", "Not Selected"))
        embed.add_field(name="Belly", value=player.belly)
        embed.add_field(
            name="Eaten Devil Fruits",
            value="\u200b" + "\n".join([f.format_name for f in player.eaten_devil_fruits]),
        )
        embed.add_field(
            name="Inventory Devil Fruits",
            value="\u200b" + "\n".join([f.format_name for f in player.inventory_devil_fruits]),
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
        embed.add_field(name="Last Seen", value=player.last_seen)
        embed.set_footer(text="UUID: {}".format(player.uuid))
        await interaction.response.send_message(embed=embed)

    @get_player.autocomplete("player")
    async def get_player_autocomplete(self, ctx, current: str):
        """Autocomplete for the player command."""
        players = list(filter(lambda x: x.name.lower().startswith(current.lower()), self.players))
        return [app_commands.Choice(name=player.name, value=player.uuid) for player in players][:25]

    @app_commands.command(name="link_player", description="Link a player to a discord account.")
    async def link_player(self, interaction, *, player: str):
        """Links a player to a discord account."""
        player: PlayerData = get(self.players, uuid=player)
        await db.players.update_player_discord_id(self.bot.db, player.uuid, interaction.user.id)
        await interaction.response.send_message("Player linked to discord account.")

    @link_player.autocomplete("player")
    async def link_player_autocomplete(self, ctx, current: str):
        """Autocomplete for the player command."""
        players = list(filter(lambda x: x.name.lower().startswith(current.lower()), self.players))
        return [app_commands.Choice(name=player.name, value=player.uuid) for player in players][:25]

    @app_commands.command(name="check_mob_kills", description="Get player mob kills.")
    async def get_mob_kills(self, interaction, *, player: str):
        """Gets a player's mob kills."""
        player: PlayerData = get(self.players, uuid=player)
        embed = Embed(title=player.name, description="```\n")
        if items := sorted(player.mob_kills.items(), key=lambda x: x[1], reverse=True):
            for mob, count in items:
                mob_name = mob.split(":")[1].replace("_", " ").title()
                embed.description += "{:<6}: {}\n".format(count, mob_name)
        else:
            embed.description += "No mob kills.\n"
        embed.description += f"```\nTotal Mob Kills: {sum(player.mob_kills.values())}"
        embed.set_footer(text="UUID: {}".format(player.uuid))
        await interaction.response.send_message(embed=embed)

    @get_mob_kills.autocomplete("player")
    async def get_mob_kills_autocomplete(self, ctx, current: str):
        """Autocomplete for the player command."""
        players = list(filter(lambda x: x.name.lower().startswith(current.lower()), self.players))
        return [app_commands.Choice(name=player.name, value=player.uuid) for player in players][:25]

    @app_commands.command(name="inactive_players", description="Get inactive players.")
    async def get_inactive_players(self, interaction, fruit: bool = False):
        """Gets a list of inactive players."""
        now = datetime.utcnow()
        embed = Embed(title="Inactive Players")
        embed.description = "```\n"
        for player in self.players:
            if now > player.last_seen + timedelta(days=3):
                if fruit and not player.devil_fruits:
                    continue
                embed.description += f"{player.name}\n"
        embed.description += "```"
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Players(bot))
