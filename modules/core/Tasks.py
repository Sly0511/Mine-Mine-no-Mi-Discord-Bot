from io import BytesIO
import json
from datetime import datetime, timedelta
from pathlib import Path
import re

from discord.ext import commands, tasks
from discord.utils import get
from nbt.nbt import NBTFile
from utils.converters import get_uuid_from_parts
from utils.functions import convert_nbt_to_dict, download_ftp_file, get_mc_player
from utils.objects import DevilFruit, PlayerData


class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.fruits = list(
            self.list_devil_fruits(json.load(open("resources/fruits.json")))
        )
        self.nbt_path = "{0}/data/mineminenomi.dat".format(self.bot.config.world_name)
        self.player_data_path = "{0}/playerdata/".format(self.bot.config.world_name)

    async def cog_load(self):
        self.read_mmnm_player_data.start()

    async def cog_unload(self):
        self.read_mmnm_player_data.cancel()

    @tasks.loop(seconds=30)
    async def read_mmnm_player_data(self):
        """Reads player data every seconds."""
        await self.bot.modules_ready.wait()
        players = []
        for player_data in self.bot.constants.FTPServer.listdir(self.player_data_path):
            if not player_data.endswith(".dat"):
                continue
            cache_file = Path("cache/player_data/{0}".format(player_data))
            nbt_bytes = download_ftp_file(
                self.bot.constants.FTPServer,
                self.player_data_path + player_data,
                cache_file,
            )
            nbt_data = convert_nbt_to_dict(NBTFile(fileobj=BytesIO(nbt_bytes)))
            forgeCaps = nbt_data.get("ForgeCaps", {})
            if not forgeCaps:
                continue
            # Devil Fruits
            eaten_devil_fruits = []
            if fruit := get(
                self.fruits,
                qualified_name=forgeCaps["mineminenomi:devil_fruit"]["devilFruit"],
            ):
                eaten_devil_fruits.append(fruit)
            yami = forgeCaps["mineminenomi:devil_fruit"]["hasYamiPower"]
            if yami:
                eaten_devil_fruits.append(get(self.fruits, qualified_name="yami_yami"))
            inventory_devil_fruits = []
            for item in nbt_data["Inventory"]:
                if re.match(r"mineminenomi:([a-z_]+no_mi)", item["id"]):
                    inventory_devil_fruits.append(
                        get(self.fruits, name=item["id"].split(":")[1])
                    )
            # Player Stats
            stats = forgeCaps["mineminenomi:entity_stats"]
            haki_stats = forgeCaps["mineminenomi:haki_data"]
            abilities = forgeCaps["mineminenomi:ability_data"]["unlocked_abilities"]
            haoshoku = bool([x for x in abilities if x["name"] == "haoshoku_haki"])
            uuid = get_uuid_from_parts(nbt_data["UUIDMost"], nbt_data["UUIDLeast"])
            mc_data = await get_mc_player(
                self.bot.db, self.bot.constants.RSession, uuid
            )
            player = PlayerData(
                uuid=uuid,
                name=mc_data.name,
                race=stats["race"] or None,
                sub_race=stats["subRace"] or None,
                faction=stats["faction"] or None,
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
            )
            players.append(player)
        self.bot.dispatch("player_data", players)

    def list_devil_fruits(self, data: dict):
        """List all devil fruits."""
        for rarity, fruits in data.items():
            for fruit in fruits:
                for qualified_name, devil_fruit in fruit.items():
                    yield DevilFruit(
                        rarity=rarity, qualified_name=qualified_name, **devil_fruit
                    )


async def setup(bot):
    await bot.add_cog(Tasks(bot))
