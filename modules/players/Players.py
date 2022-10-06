from datetime import datetime, timedelta
from io import BytesIO
from random import randint
from uuid import UUID

import matplotlib.pyplot as plt
from discord import ButtonStyle, Embed, File, app_commands
from discord.ext import commands
from discord.ui import Modal, TextInput, View, button
from discord.utils import get
from mcrcon import MCRcon, MCRconException
from utils.database.models import Players as PlayersDB
from utils.objects import Factions, FightingStyles, Races, PlayerData


class InsertCodeModal(Modal, title="Code Input"):
    sent_code = TextInput(
        label="Input the code that you were sent in-game", min_length=4, max_length=4, placeholder="1234"
    )

    def __init__(self, bot, player, code: int):
        super().__init__()
        self.bot = bot
        self.player = player
        self.code = code

    async def on_submit(self, interaction) -> None:
        try:
            if int(self.sent_code.value) != self.code:
                raise Exception("Wrong!")
            prev_link = await PlayersDB.find_one(PlayersDB.discord_id == interaction.user.id)
            player = await PlayersDB.find_one(PlayersDB.name == self.player[0])
            if player is None:
                await PlayersDB(uuid=self.player[1], name=self.player[0]).insert()
            player = await PlayersDB.find_one(PlayersDB.name == self.player[0])
            if prev_link:
                if prev_link.uuid == player.uuid:
                    return await interaction.response.send_message("You have already linked your discord account.")
                else:
                    return await interaction.response.send_message(
                        "This discord account is already linked to another player."
                    )
            if player.discord_id:
                return await interaction.response.send_message("You already linked an account.")
            player.discord_id = interaction.user.id
            await player.save()
            await interaction.response.send_message("Player linked to discord account.")
        except ValueError:
            return await interaction.response.send_message("The value input was not correct.")


class CodeButton(View):
    def __init__(self, bot, player, code):
        super().__init__()
        self.bot = bot
        self.player = player
        self.code = code

    async def interaction_check(self, interaction):
        if self.player[2].id != interaction.user.id:
            await interaction.response.send_message("You can't interact with this button.", ephemeral=True)
            return False
        return True

    @button(label="Input code", style=ButtonStyle.green)
    async def submit_code(self, interaction, button):
        await interaction.response.send_modal(InsertCodeModal(self.bot, self.player, self.code))
        self.stop()


class Players(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.players = []

    @commands.Cog.listener("on_player_data")
    async def update_player_data(self, player_data: list[PlayerData]):
        """Updates the devil fruit circulation."""
        await self.bot.modules_ready.wait()
        self.players = player_data
        guild = self.bot.get_guild(self.bot.config.discord_server_id)
        if not guild:
            return
        for player in player_data:
            member = guild.get_member(player.discord_id)
            if not member:
                continue
            if member.display_name != player.name:
                try:
                    await member.edit(nick=player.name)
                except:
                    pass

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
        # embed.add_field(name="Doriki", value=player.doriki)
        # embed.add_field(
        #     name="Loyalty",
        #     value=player.loyalty if player.faction == Factions.Marine else "N/A",
        # )
        # embed.add_field(name="Bounty", value=player.bounty)
        # embed.add_field(
        #     name="Haki",
        #     value=(
        #         f"Hardening: {player.harderning_haki}\n"
        #         + f"Imbuing: {player.imbuing_haki}\n"
        #         + f"Observation: {player.observation_haki}\n"
        #         + f"Conquerors: "
        #         + ("Yes\n" if player.haoshoku_haki else "No\n")
        #         + f"Haki Limit: {player.haki_limit}\n"
        #     ),
        # )
        embed.set_footer(text="UUID: {}".format(player.uuid))
        await interaction.response.send_message(embed=embed)

    @get_player.autocomplete("player")
    async def get_player_autocomplete(self, ctx, current: str):
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

    @app_commands.command(name="factions_population", description="Shows population distribution across factions.")
    async def get_factions_population(self, interaction):
        pirates = [p for p in self.players if p.faction == Factions.Pirate]
        marines = [p for p in self.players if p.faction == Factions.Marine]
        revolut = [p for p in self.players if p.faction == Factions.Revolutionary]
        bounthr = [p for p in self.players if p.faction == Factions.BountyHunter]
        populations = [len(pirates), len(marines), len(revolut), len(bounthr)]
        labels = ["Pirates", "Marines", "Revolutionaries", "Bounty hunters"]
        colors = ["#6b0700", "#00276b", "#8a2801", "#256b00"]
        _, ax1 = plt.subplots()
        _, texts, autotexts = ax1.pie(populations, colors=colors, labels=labels, autopct="%1.1f%%", startangle=90)
        for text in texts:
            text.set_color("#ccc")
        for autotext in autotexts:
            autotext.set_color("#ccc")
        centre_circle = plt.Circle((0, 0), 0.70, fc="#0000")
        fig = plt.gcf()
        fig.gca().add_artist(centre_circle)
        ax1.axis("equal")
        image = BytesIO()
        plt.savefig(image, facecolor="#0000", format="PNG")
        image.seek(0)
        await interaction.response.send_message(file=File(image, filename="factions.png"))

    @app_commands.command(
        name="fighting_styles_population", description="Shows population distribution across fighting styles."
    )
    async def get_fighting_styles_population(self, interaction):
        swordsman = [p for p in self.players if p.fighting_style == FightingStyles.Swordsman]
        sniper = [p for p in self.players if p.fighting_style == FightingStyles.Sniper]
        doctor = [p for p in self.players if p.fighting_style == FightingStyles.Doctor]
        brawler = [p for p in self.players if p.fighting_style == FightingStyles.Brawler]
        blackleg = [p for p in self.players if p.fighting_style == FightingStyles.BlackLeg]
        artofweather = [p for p in self.players if p.fighting_style == FightingStyles.ArtofWeather]
        populations = [len(swordsman), len(sniper), len(doctor), len(brawler), len(blackleg), len(artofweather)]
        labels = ["Swordsman", "Sniper", "Doctor", "Brawler", "Black Leg", "Art of Weather"]
        _, ax1 = plt.subplots()
        _, texts, autotexts = ax1.pie(populations, labels=labels, autopct="%1.1f%%", startangle=90)
        for text in texts:
            text.set_color("#ccc")
        for autotext in autotexts:
            autotext.set_color("#ccc")
        centre_circle = plt.Circle((0, 0), 0.70, fc="#0000")
        fig = plt.gcf()
        fig.gca().add_artist(centre_circle)
        ax1.axis("equal")
        image = BytesIO()
        plt.savefig(image, facecolor="#0000", format="PNG")
        image.seek(0)
        await interaction.response.send_message(file=File(image, filename="fighting_styles.png"))

    @app_commands.command(name="races_population", description="Shows population distribution across races.")
    async def get_fighting_styles_population(self, interaction):
        human = [p for p in self.players if p.race == Races.Human]
        cyborg = [p for p in self.players if p.race == Races.Cyborg]
        mink = [p for p in self.players if p.race == Races.Mink]
        fishman = [p for p in self.players if p.race == Races.Fishman]
        populations = [len(human), len(cyborg), len(mink), len(fishman)]
        labels = ["Human", "Cyborg", "Mink", "Fishman"]
        _, ax1 = plt.subplots()
        _, texts, autotexts = ax1.pie(populations, labels=labels, autopct="%1.1f%%", startangle=90)
        for text in texts:
            text.set_color("#ccc")
        for autotext in autotexts:
            autotext.set_color("#ccc")
        centre_circle = plt.Circle((0, 0), 0.70, fc="#0000")
        fig = plt.gcf()
        fig.gca().add_artist(centre_circle)
        ax1.axis("equal")
        image = BytesIO()
        plt.savefig(image, facecolor="#0000", format="PNG")
        image.seek(0)
        await interaction.response.send_message(file=File(image, filename="races.png"))

    @app_commands.command(name="link_player", description="Link a player to a discord account.")
    async def link_player(self, interaction, *, player: str):
        """Links a player to a discord account."""
        await interaction.response.defer()
        async with self.bot.constants.RSession.get(f"https://api.mojang.com/users/profiles/minecraft/{player}") as p:
            if p.status in (204, 400):
                return await interaction.response.send_message("Please provide a valid username.")
            player = await p.json()
            player = (player["name"], str(UUID(player["id"])), interaction.user)
        code = randint(1000, 9999)
        with MCRcon(
            host=self.bot.config.rcon_ip, password=self.bot.config.rcon_password, port=self.bot.config.rcon_port
        ) as rcon:
            try:
                rcon.command(f"/msg {player[0]} Your Discord link code: {code}")
            except MCRconException:
                return await interaction.followup.send(f"The {self.bot.config.server_name} server isn't responding.")
        embed = Embed(title="Discord Account Link")
        embed.description = (
            'A code was sent to you via private message in minecraft. Click "Input code" and put the code in the box.'
        )
        await interaction.followup.send(view=CodeButton(self.bot, player, code), embed=embed, ephemeral=True)

    @link_player.autocomplete("player")
    async def link_player_autocomplete(self, ctx, current: str):
        """Autocomplete for the player command."""
        players = list(filter(lambda x: x.name.lower().startswith(current.lower()), self.players))
        return [app_commands.Choice(name=player.name, value=player.name) for player in players][:25]


async def setup(bot):
    await bot.add_cog(Players(bot))
