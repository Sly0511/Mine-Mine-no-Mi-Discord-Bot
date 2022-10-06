import asyncio
import gzip
import json
import re
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from random import sample

from discord import Interaction, app_commands
from discord.ext import commands, tasks
from discord.utils import get
from nbt.nbt import NBTFile
from utils.converters import get_uuid_from_parts
from utils.functions import convert_nbt_to_dict, open_file, get_mc_player
from utils.objects import DevilFruit, PlayerData


class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.fruits = list(self.list_devil_fruits(json.load(open("resources/fruits.json"))))
        self.nbt_path = Path(f"/default/{self.bot.config.world_name}/data/mineminenomi.dat")
        self.player_data_path = Path(f"/default/{self.bot.config.world_name}/playerdata/")
        self.cache_player_data_path = Path(f"/home/{self.bot.config.linux_user}/MMnM/cache/player_data/")
        self.player_stats_path = Path(f"/default/{self.bot.config.world_name}/stats/")
        self.logs_path = Path(f"default/logs")
        self.players = []

    async def cog_load(self):
        self.read_mmnm_player_data.start()
        self.retrieve_logs.start()

    async def cog_unload(self):
        self.read_mmnm_player_data.cancel()
        self.retrieve_logs.cancel()

    @tasks.loop(seconds=30)
    async def read_mmnm_player_data(self):
        """Reads player data every seconds."""
        await self.bot.modules_ready.wait()
        guild = self.bot.get_guild(self.bot.config.discord_server_id)
        if not guild:
            return
        linked_role = guild.get_role(self.bot.config.link_role)
        players = []
        username_cache = json.loads(await self.bot.FTPServer.get_file(f"/default/usernamecache.json"))
        mineminenomi_bytes = await self.bot.FTPServer.get_file(self.nbt_path)
        mineminenomi_data = convert_nbt_to_dict(NBTFile(fileobj=BytesIO(mineminenomi_bytes)))
        timed_out_fruits = {
            get_uuid_from_parts(inventory["uuidMost"], inventory["uuidLeast"]): [
                get(self.fruits, qualified_name=inventory[f"fruit-{fruit_n}"]) for fruit_n in range(inventory["fruits"])
            ]
            for inventory in mineminenomi_data["data"]["loggedoutFruits"]
            if inventory["date"] / 1000 < (datetime.utcnow() - timedelta(days=3)).timestamp()
        }
        now = datetime.utcnow()
        await self.bot.FTPServer.download_player_data(self.player_data_path)
        for player_data in self.cache_player_data_path.glob("*.dat"):
            last_time = datetime.utcfromtimestamp(int(player_data.lstat().st_mtime))
            if old_player := get(self.players, uuid=player_data.stem):
                if last_time < now - timedelta(days=5):
                    players.append(old_player)
                    continue
            nbt_bytes = open_file(self.cache_player_data_path.joinpath(player_data))
            nbt_data = convert_nbt_to_dict(NBTFile(fileobj=BytesIO(nbt_bytes)))
            player_uuid = player_data.stem
            stats_data = await self.bot.FTPServer.get_file(self.player_stats_path.joinpath(f"{player_uuid}.json"))
            stats_data = json.loads(stats_data)
            forgeCaps = nbt_data.get("ForgeCaps", {})
            if not forgeCaps:
                continue
            # Devil Fruits
            eaten_devil_fruits = []
            inventory_devil_fruits = []
            if not timed_out_fruits.get(player_uuid):
                yami = forgeCaps["mineminenomi:devil_fruit"]["hasYamiPower"]
                if fruit := get(
                    self.fruits,
                    qualified_name=forgeCaps["mineminenomi:devil_fruit"].get("devilFruit", ""),
                ):
                    eaten_devil_fruits.append(fruit)
                if yami:
                    eaten_devil_fruits.append(get(self.fruits, qualified_name="yami_yami"))
                for item in nbt_data["Inventory"]:
                    if re.match(r"mineminenomi:([a-z_]+no_mi)", item["id"]):
                        inventory_devil_fruits.append(get(self.fruits, name=item["id"].split(":")[1]))
            # Player Stats
            stats = forgeCaps["mineminenomi:entity_stats"]
            haki_stats = forgeCaps["mineminenomi:haki_data"]
            abilities = forgeCaps["mineminenomi:ability_data"]["unlocked_abilities"]
            haoshoku = bool([x for x in abilities if x["name"] == "haoshoku_haki"])
            uuid = get_uuid_from_parts(nbt_data["UUIDMost"], nbt_data["UUIDLeast"])
            mc_data = await get_mc_player(username_cache, uuid)
            total_haki = (
                haki_stats["busoHardeningHakiExp"] + haki_stats["busoImbuingHakiExp"] + haki_stats["kenHakiExp"]
            )
            player = PlayerData(
                uuid=uuid,
                name=mc_data.name,
                race=stats["race"] or None,
                sub_race=stats["subRace"] or None,
                faction=stats["faction"] or None,
                fighting_style=stats["fightingStyle"] or None,
                inventory=nbt_data["Inventory"],
                devil_fruits=eaten_devil_fruits + inventory_devil_fruits,
                eaten_devil_fruits=eaten_devil_fruits,
                inventory_devil_fruits=inventory_devil_fruits,
                belly=stats["belly"],
                bounty=stats["bounty"],
                loyalty=stats["loyalty"],
                doriki=stats["doriki"],
                harderning_haki=haki_stats["busoHardeningHakiExp"],
                imbuing_haki=haki_stats["busoImbuingHakiExp"],
                observation_haki=haki_stats["kenHakiExp"],
                haoshoku_haki=haoshoku,
                haki_limit=round(2200 + (total_haki * 32), 1),
                mob_kills=stats_data.get("stats", {}).get("minecraft:killed", {}),
                discord_id=mc_data.discord_id,
                last_seen=last_time,
                inactive=last_time < now - timedelta(days=5),
            )
            players.append(player)
            if player.discord_id is not None and linked_role:
                member = guild.get_member(player.discord_id)
                if member and linked_role not in member.roles:
                    asyncio.create_task(member.add_roles(linked_role))
        self.bot.dispatch("player_data", players)
        self.players = players

    # @read_mmnm_player_data.error()
    # async def test(self, **kwargs):
    #     print(kwargs)

    @tasks.loop(minutes=5)
    async def retrieve_logs(self):
        """Retrieves logs every 5 minutes."""
        await self.bot.modules_ready.wait()
        return
        logs = []
        for log in self.logs_path.iterdir():
            bytes_data = open_file(log)
            log_string = re.search(r"(\d{4}-\d{2}-\d{2})-(\d{1,2})", log)
            if log_string is None:
                if log == "latest.log":
                    log_date = datetime.utcnow()
                    index = 0
                else:
                    continue
            else:
                log_date = datetime.strptime(log_string.group(1), "%Y-%m-%d")
                index = log_string.group(2)
            log_data = {"name": log, "date": log_date, "index": index, "lines": []}

            def remove_IP(line):
                return re.sub(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", "*", line)

            if log.endswith(".log.gz"):
                data = gzip.GzipFile(fileobj=BytesIO(bytes_data))
                log_text = data.read().decode("utf-8")
                for line in log_text.split("\n"):
                    if not line:
                        continue
                    log_data["lines"].append(remove_IP(line))
            elif log.endswith(".log"):
                log_text = bytes_data.decode("utf-8")
                for line in log_text.split("\n"):
                    if not line:
                        continue
                    log_data["lines"].append(remove_IP(line))
            logs.append(log_data)
        self.bot.dispatch("logs_read", sorted(logs, key=lambda x: (x["date"], x["index"])))

    def list_devil_fruits(self, data: dict):
        """List all devil fruits."""
        for rarity, fruits in data.items():
            for fruit in fruits:
                for qualified_name, devil_fruit in fruit.items():
                    yield DevilFruit(rarity=rarity, qualified_name=qualified_name, **devil_fruit)

    @app_commands.command(name="random_player")
    async def random_player(self, interaction: Interaction, size: int = 1):
        """Random player."""
        try:
            players = sample([p for p in self.players if p.last_seen > datetime.utcnow() - timedelta(days=2)], k=size)
        except ValueError:
            return await interaction.response.send_message("Not enough players to satisfy {} request.".format(size))
        await interaction.response.send_message(
            "\n".join(["`{1}` - **{0}**".format(player.name, player.uuid).replace("_", "\_") for player in players])
        )


async def setup(bot):
    await bot.add_cog(Tasks(bot))
