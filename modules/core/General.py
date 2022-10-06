from json import dumps, load, loads
from pathlib import Path

from discord import Embed, Attachment, app_commands, File
from discord.ext import commands
from mcrcon import MCRcon
from utils.objects import PlayerData
from utils.checks import is_bot_owner_interaction
import re
from io import BytesIO

import numpy as np


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.players = []

    @commands.Cog.listener("on_player_data")
    async def update_player_data(self, player_data: list[PlayerData]):
        """Updates the devil fruit circulation."""
        await self.bot.modules_ready.wait()
        self.players = player_data

    @app_commands.command(name="mods")
    async def mods(self, interaction):
        """
        Lists all mods installed on the server.
        """
        mods = Path("/home/gVQZjCoEIG/Lost Island/client/mods".format(self.bot.config.world_name))
        embed = Embed(
            title=f"Mods in {self.bot.config.server_name} server",
            description=f"[Download Modpack]({self.bot.config.modpack_download})\nServer IP: `{self.bot.config.server_ip}:{self.bot.config.server_port}`\n",
        )
        embed.description += (
            "```\n"
            + "\n".join(
                [mod.name for mod in sorted(mods.iterdir(), key=lambda x: x.name.lower()) if mod.suffix == ".jar"]
            )
            + "\n```"
        )
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
            host=self.bot.config.rcon_ip, password=self.bot.config.rcon_password, port=self.bot.config.rcon_port
        ) as rcon:
            response = rcon.command(f"/{command}")
            await interaction.response.send_message(response or "Command ran successfully")

    @app_commands.command(name="flag", description="Set flags for a region")
    @is_bot_owner_interaction()
    async def flag(self, interaction, protect: bool, region: str):
        await interaction.response.defer()
        flags = [
            "break",
            "place",
            "chest-access",
            "explosions",
            "creeper-explosions",
            "enderpearls",
            "exp-drop",
            "other-explosions",
            "fall-damage",
            "invincible",
            "item-drop",
            "mob-spawning-all",
            "damage-players",
            "damage-monsters",
            "damage-animals",
        ]
        with MCRcon(
            host=self.bot.config.rcon_ip, password=self.bot.config.rcon_password, port=self.bot.config.rcon_port
        ) as rcon:
            mode = "add" if protect else "remove"
            for flag in flags:
                rcon.command(f"/execute as @a run flag {mode} {region} {flag}")
        await interaction.followup.send("Flags were changed!")

    @app_commands.command(name="summon_trader", description="Spawn a custom trader.")
    @is_bot_owner_interaction()
    async def summon_trader(self, interaction, name: str, position: str, trades_file: Attachment, rotation: int = 0):
        await interaction.response.defer()
        trades_data = loads(await trades_file.read())
        trades = dumps(trades_data, separators=(",", ":"), ensure_ascii=False)
        trade_wrapper = r'{"CustomNameVisible":1b,"Silent":1b,"Rotation":[$rotation$f,0f],"NoAI":1b,"CustomName":"{\"text\":\"$name$\",\"color\":\"white\"}","Invulnerable":1b,"Offers":{"Recipes":$trades$}}'
        command = re.sub(
            r'("belly":[0-9]+)',
            r"\1L",
            f"/summon goblintraders:goblin_trader {position} "
            + trade_wrapper.replace("$trades$", trades)
            .replace("$rotation$", str(rotation))
            .replace("$name$", name)
            .replace("\u00A7", "§"),
        )
        data = BytesIO()
        data.write(command.encode())
        data.seek(0)
        await interaction.followup.send(file=File(data, filename="command.txt"))

    @app_commands.command(name="restore_stats", description="Restore haki/doriki/belly stats.")
    @is_bot_owner_interaction()
    async def restore_stats(
        self,
        interaction,
        player: str,
        doriki: int = 0,
        belly: int = 0,
        hardening: float = 0.0,
        imbuing: float = 0.0,
        observation: float = 0.0,
        rotations: int = 1,
    ):
        await interaction.response.defer()
        with MCRcon(
            host=self.bot.config.rcon_ip, password=self.bot.config.rcon_password, port=self.bot.config.rcon_port
        ) as rcon:
            for _ in range(rotations):
                if doriki:
                    adoriki = doriki / 0.66 - doriki
                    doriki += adoriki
                    rcon.command(f"/doriki {int(adoriki)} {player}")
                if belly:
                    abelly = belly / 0.66 - belly
                    belly += abelly
                    rcon.command(f"/belly {int(abelly)} {player}")
                if hardening:
                    ahardening = hardening / 0.75 - hardening
                    hardening += ahardening
                    rcon.command(f"/hakiexp HARDENING {ahardening} {player}")
                if imbuing:
                    aimbuing = imbuing / 0.75 - imbuing
                    imbuing += aimbuing
                    rcon.command(f"/hakiexp IMBUING {aimbuing} {player}")
                if observation:
                    aobservation = observation / 0.75 - observation
                    observation += aobservation
                    rcon.command(f"/hakiexp KENBUNSHOKU {aobservation} {player}")
        await interaction.followup.send("Stats restored.")

    @restore_stats.autocomplete("player")
    async def restore_stats_autocomplete(self, ctx, current: str):
        """Autocomplete for the player command."""
        players = list(filter(lambda x: x.name.lower().startswith(current.lower()), self.players))
        return [app_commands.Choice(name=player.name, value=player.name) for player in players][:25]

    @app_commands.command(name="summon_trainer")
    @app_commands.checks.cooldown(1, 900.0, key=lambda i: i.user.id)
    async def summon_trainer(self, interaction, player: str, trainer: str):
        await interaction.response.defer()
        with MCRcon(
            host=self.bot.config.rcon_ip, password=self.bot.config.rcon_password, port=self.bot.config.rcon_port
        ) as rcon:
            noAI = "{NoAI:1}"
            response = rcon.command(f"/execute at {player} run summon {trainer} ~ ~ ~ {noAI}")
            await interaction.followup.send(response)

    @summon_trainer.autocomplete("player")
    async def summon_trainer_player_autocomplete(self, ctx, current: str):
        """Autocomplete for the player command."""
        players = list(filter(lambda x: x.name.lower().startswith(current.lower()), self.players))
        return [app_commands.Choice(name=player.name, value=player.name) for player in players][:25]

    @summon_trainer.autocomplete("trainer")
    async def summon_trainer_trainer_autocomplete(self, ctx, current: str):
        """Autocomplete for the player command."""
        trainers = {
            "Black Leg": "mineminenomi:black_leg_trainer",
            "Bow Master": "mineminenomi:bow_master",
            "Brawler": "mineminenomi:brawler",
            "Doctor": "mineminenomi:doctor",
            "Dojo Sensei": "mineminenomi:dojo_sensei",
            "Weather Wizard": "mineminenomi:weather_wizard",
        }
        trainers = list(filter(lambda x: x[0].lower().startswith(current.lower()), trainers.items()))
        return [app_commands.Choice(name=trainer[0], value=trainer[1]) for trainer in trainers][:25]

    @app_commands.command(name="wave", description="Start a wave at the wave arena.")
    async def wave(self, interaction):
        coords = ""

    def get_points(self, radius, number_of_points, x=0, y=0):
        radians_between_each_point = 2 * np.pi / number_of_points
        for p in range(0, number_of_points):
            yield (
                int(radius * np.cos(p * radians_between_each_point) + x),
                int(radius * np.sin(p * radians_between_each_point) + y),
            )

    @app_commands.command(name="boss_rewards")
    @is_bot_owner_interaction()
    async def boss_rewards(self, interaction, player: str, boss: str, amount: int, haki_type: str):
        ...

    @boss_rewards.autocomplete("boss")
    async def boss_rewards_boss_autocomplete(self, ctx, current: str):
        """Autocomplete for the player command."""
        bosses = {
            "Frostmaw": "mowziesmobs:frostmaw",
            "Ferrous Wroughtnaut": "mowziesmobs:ferrous_wroughtnaut",
            "Barako": "mowziesmobs:barako",
            "Naga": "mowziesmobs:naga",
        }
        bosses = list(filter(lambda x: x[0].lower().startswith(current.lower()), bosses.items()))
        return [app_commands.Choice(name=boss[0], value=boss[1]) for boss in bosses][:25]


async def setup(bot):
    await bot.add_cog(General(bot))
