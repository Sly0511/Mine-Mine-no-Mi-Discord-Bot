import asyncio
import json
from io import BytesIO
from random import choice, choices

import matplotlib.pyplot as plt
from discord import Embed, File, Member, app_commands
from discord.ext import commands
from discord.utils import get
from mcrcon import MCRcon
from utils.checks import is_bot_admin_interaction
from utils.objects import PlayerData, Race, Bloodline, Rarities


class RacesAndBloodlines(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_data()
        self.players = []

    async def cog_load(self):
        asyncio.create_task(self.check_all())

    async def check_all(self):
        await self.bot.modules_ready.wait()
        guild = self.bot.get_guild(self.bot.config.discord_server_id)
        if guild:
            for member in guild.members:
                await self.check_race_and_blood(member)

    def load_data(self):
        self.users_data = json.load(open("modules/races_and_bloodlines/users_data.json", "r"))
        races = json.load(open("modules/races_and_bloodlines/races.json", "r"))
        self.races = [Race(**r) for r in races]
        bloodlines = json.load(open("modules/races_and_bloodlines/bloodlines.json", "r"))
        self.bloodlines = [Bloodline(**b) for b in bloodlines]

    @commands.Cog.listener("on_player_data")
    async def update_player_data(self, player_data: list[PlayerData]):
        """Updates the devil fruit circulation."""
        await self.bot.modules_ready.wait()
        self.players = player_data

    @commands.Cog.listener("on_member_join")
    async def enforce_race_blood(self, member):
        user_data = self.users_data.get(str(member.id))
        if user_data is None:
            return
        race = user_data.get("race")
        blood = user_data.get("blood")
        for race_blood in self.races + self.bloodlines:
            if race_blood.name in [race, blood]:
                await member.add_roles(member.guild.get_role(race_blood.role))

    @commands.Cog.listener("on_member_update")
    async def on_member_update(self, before, after):
        if before.roles == after.roles:
            return
        await self.check_race_and_blood(after)

    @app_commands.command(name="roll_race_blood", description="Roll your race and bloodline.")
    async def roll_race_and_bloodlines(self, interaction):
        user_data = self.users_data.get(str(interaction.user.id), {"race": None, "blood": None})
        # Races
        if user_data.get("race") is None:
            race_tier = self.get_random_race_tier(interaction.user)
            races = [r for r in self.races if r.tier == race_tier]
            race = choice(races)
            user_data["race"] = race.name
            await interaction.user.add_roles(interaction.guild.get_role(race.role))
        else:
            race = [r for r in self.races if r.name == user_data["race"]][0]
        # Bloodlines
        if user_data.get("blood") is None:
            blood_tier = self.get_random_blood_tier(interaction.user)
            bloods = [b for b in self.bloodlines if b.tier == blood_tier]
            blood = choice(bloods)
            user_data["blood"] = blood.name
            await interaction.user.add_roles(interaction.guild.get_role(blood.role))
        else:
            blood = [b for b in self.bloodlines if b.name == user_data["blood"]][0]
        self.users_data[str(interaction.user.id)] = user_data
        self.save_race_blood_data()
        await interaction.response.send_message(f"Race: **{race.Rformat_name}**\nBlood: **{blood.Rformat_name}**")

    def get_random_race_tier(self, member):
        guild = member.guild
        if guild.get_role(self.bot.config.patreon_role) in member.roles:
            weights = [18, 42, 35, 5]
        elif member.premium_since is not None:
            weights = [15, 30, 45, 10]
        else:
            weights = [11, 22, 53, 14]
        return choices([1, 2, 3, 4], weights=weights, k=1)[0]

    def get_random_blood_tier(self, member):
        guild = member.guild
        if guild.get_role(self.bot.config.patreon_role) in member.roles:
            weights = [10, 18, 27, 30, 15]
        elif member.premium_since is not None:
            weights = [7, 10, 18, 30, 35]
        else:
            weights = [5, 10, 15, 25, 45]
        return choices([1, 2, 3, 4, 5], weights=weights, k=1)[0]

    @app_commands.command(name="set_race_blood", description="Set someone's race or bloodline into something else.")
    @is_bot_admin_interaction()
    async def set_race_blood(self, interaction, user: Member, race: str = None, blood: str = None):
        if not race and not blood:
            return await interaction.response.send_message(
                "Please select whether to set race and/or blood.", ephemeral=True
            )
        user_data = self.users_data.get(str(user.id), {"race": None, "blood": None})
        if race is not None:
            races = [r.name for r in self.races]
            if race not in races:
                return await interaction.response.send_message("Invalid race. No changes were done.")
            user_data["race"] = race
        if blood is not None:
            bloods = [b.name for b in self.bloodlines]
            if blood not in bloods:
                return await interaction.response.send_message("Invalid bloodline. No changes were done.")
            user_data["blood"] = blood
        self.users_data[str(user.id)] = user_data
        self.save_race_blood_data()
        await self.check_race_and_blood(user)
        await interaction.response.send_message("Changes were applied.", ephemeral=True)

    @set_race_blood.autocomplete("race")
    async def set_race_blood_race_autocomplete(self, interaction, current: str):
        races = filter(lambda x: x.name.lower().startswith(current.lower()), sorted(self.races, key=lambda x: x.name))
        return [app_commands.Choice(name=r.Rformat_name, value=r.name) for r in races][:25]

    @set_race_blood.autocomplete("blood")
    async def set_race_blood_blood_autocomplete(self, interaction, current: str):
        bloodlines = filter(
            lambda x: x.name.lower().startswith(current.lower()), sorted(self.bloodlines, key=lambda x: x.name)
        )
        return [app_commands.Choice(name=b.Rformat_name, value=b.name) for b in bloodlines][:25]

    @app_commands.command(name="reset_race_blood", description="Reset someone's race or bloodline.")
    @is_bot_admin_interaction()
    async def reset_race_blood(self, interaction, user: Member, race: bool, blood: bool):
        if not race and not blood:
            return await interaction.response.send_message(
                "Please select whether to reset race and/or blood.", ephemeral=True
            )
        user_data = self.users_data.get(str(user.id), {"race": None, "blood": None})
        if race:
            user_data["race"] = None
        if blood:
            user_data["blood"] = None
        self.users_data[str(user.id)] = user_data
        self.save_race_blood_data()
        await self.check_race_and_blood(user)
        await interaction.response.send_message(f"Successfully reset {user.mention}.", ephemeral=True)

    @app_commands.command(name="bloodline", description="Get bloodline info.")
    async def check_bloodline(self, interaction, name: str):
        blood = get(self.bloodlines, name=name)
        if not blood:
            return await interaction.response.send_message("Invalid bloodline.")
        blood = blood[0]
        embed = Embed(title=blood.Rformat_name, description="\n".join(blood.stats), color=0x00FF00)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @check_bloodline.autocomplete("name")
    async def set_race_blood_blood_autocomplete(self, interaction, current: str):
        bloodlines = filter(
            lambda x: x.name.lower().startswith(current.lower()), sorted(self.bloodlines, key=lambda x: x.name)
        )
        return [app_commands.Choice(name=b.Rformat_name, value=b.name) for b in bloodlines][:25]

    @app_commands.command(name="give_bloodline_charm", description="Give a player their bloodline charm")
    @is_bot_admin_interaction()
    async def give_bloodline_charm(self, interaction, player: str):
        player: PlayerData = get(self.players, uuid=player)
        if not player.discord_id:
            return await interaction.response.send_message(
                "That player hasn't connected their account to discord.", ephemeral=True
            )
        user = await self.bot.fetch_user(player.discord_id)
        data = self.users_data.get(str(user.id), {"race": None, "blood": None})
        if data.get("blood") is None:
            return await interaction.response.send_message("That player hasn't rolled their bloodline.")
        blood = get(self.bloodlines, name=data["blood"])
        with MCRcon(
            host=self.bot.config.server_ip, password=self.bot.config.rcon_password, port=self.bot.config.rcon_port
        ) as rcon:
            charm = r'apotheosis:potion_charm{Unbreakable:1b,Enchantments:[{lvl:1,id:binding_curse}],display:{Lore:["{\"text\": \"\"}","{\"text\": \"§fBloodline\"}","{\"text\": \"$1$2\"}"],Name:"{\"text\":\"$3\"}"}}'
            charm = charm.replace("$1", blood.mc_color).replace("$2", blood.tier_name).replace("$3", blood.name)
            response = rcon.command(f"/give {player.name} {charm}")
            await interaction.response.send_message(response)

    @give_bloodline_charm.autocomplete("player")
    async def give_bloodline_charm_autocomplete(self, ctx, current: str):
        """Autocomplete for the player command."""
        players = list(filter(lambda x: x.name.lower().startswith(current.lower()), self.players))
        return [app_commands.Choice(name=player.name, value=player.uuid) for player in players][:25]

    @app_commands.command(name="races_population", description="Shows population distribution across races.")
    async def get_races_population(self, interaction):
        await interaction.response.defer()
        data = [(r.name, len([p for p in self.users_data.values() if p.get("race") == r.name])) for r in self.races]
        data.sort(key=lambda x: x[1])
        _, ax1 = plt.subplots()
        _, texts, autotexts = ax1.pie(
            [d[1] for d in data], labels=[d[0] for d in data], autopct="%1.1f%%", startangle=90
        )
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
        await interaction.followup.send(file=File(image, filename="races.png"))

    @app_commands.command(
        name="races_rarity_population", description="Shows population distribution across race rarities."
    )
    async def get_races_rarity_population(self, interaction):
        await interaction.response.defer()
        data = {}
        for player in self.users_data.values():
            if (race_name := player.get("race")) is not None:
                race = get(self.races, name=race_name)
                if race.tier not in data.keys():
                    data[race.tier] = 0
                data[race.tier] += 1
        rarities = []
        values = []
        for tier, value in sorted(list(data.items()), key=lambda x: x[0]):
            rarities.append(Rarities(tier + 1).name)
            values.append(value)
        _, ax1 = plt.subplots()
        _, texts, autotexts = ax1.pie(list(values), labels=rarities, autopct="%1.1f%%", startangle=90)
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
        await interaction.followup.send(file=File(image, filename="race_rarities.png"))

    @app_commands.command(name="bloodlines_population", description="Shows population distribution across bloodlines.")
    async def get_bloodlines_population(self, interaction):
        await interaction.response.defer()
        data = [
            (b.name, len([p for p in self.users_data.values() if p.get("blood") == b.name])) for b in self.bloodlines
        ]
        data.sort(key=lambda x: x[1])
        _, ax1 = plt.subplots()
        _, texts, autotexts = ax1.pie(
            [d[1] for d in data], labels=[d[0] for d in data], autopct="%1.1f%%", startangle=90
        )
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
        await interaction.followup.send(file=File(image, filename="bloodlines.png"))

    @app_commands.command(
        name="bloodlines_rarity_population", description="Shows population distribution across bloodline rarities."
    )
    async def get_bloodlines_rarity_population(self, interaction):
        await interaction.response.defer()
        data = {}
        for player in self.users_data.values():
            if (blood_name := player.get("blood")) is not None:
                blood = get(self.bloodlines, name=blood_name)
                if blood.tier not in data.keys():
                    data[blood.tier] = 0
                data[blood.tier] += 1
        rarities = []
        values = []
        for tier, value in sorted(list(data.items()), key=lambda x: x[0]):
            rarities.append(Rarities(tier).name)
            values.append(value)
        _, ax1 = plt.subplots()
        _, texts, autotexts = ax1.pie(list(values), labels=rarities, autopct="%1.1f%%", startangle=90)
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
        await interaction.followup.send(file=File(image, filename="bloodline_rarities.png"))

    async def check_race_and_blood(self, member):
        guild = member.guild
        user_data = self.users_data.get(str(member.id), {"race": None, "blood": None})
        Races_and_Bloodlines = self.races + self.bloodlines
        race = user_data.get("race")
        blood = user_data.get("blood")
        Race_and_Blood = [race, blood]
        for race_blood in Races_and_Bloodlines:
            if race_blood.name not in Race_and_Blood:
                role = guild.get_role(race_blood.role)
                role_name = race_blood.format_name
                if role.name != role_name:
                    await role.edit(name=role_name)
                if role in member.roles:
                    await member.remove_roles(role)
            if race_blood.name in Race_and_Blood:
                role = guild.get_role(race_blood.role)
                role_name = race_blood.format_name
                if role.name != role_name:
                    await role.edit(name=role_name)
                if role not in member.roles:
                    await member.add_roles(role)

    def save_race_blood_data(self):
        with open("modules/races_and_bloodlines/users_data.json", "w+") as f:
            json.dump(self.users_data, f, indent=4)


async def setup(bot):
    await bot.add_cog(RacesAndBloodlines(bot))
