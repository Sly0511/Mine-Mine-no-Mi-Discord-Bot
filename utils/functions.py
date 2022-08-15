from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

import yaml
from aiohttp import ClientSession
from nbt import nbt
from nbt.nbt import TAG_Byte, TAG_Compound, TAG_Int, TAG_List, TAG_Long, TAG_String

from utils.objects import MinecraftPlayer, Module
import utils.database as db


def chunks(l: Iterable, n: int) -> Iterable:
    """Yield successive n-sized chunks from list."""
    for i in range(0, len(l), n):
        yield l[i : i + n]


def convert_nbt_to_dict(data: nbt.NBTFile) -> dict:
    """Convert nbt file to dict."""
    as_dict = {}
    for key, value in data.iteritems():
        if isinstance(value, TAG_Compound):
            as_dict[key] = convert_nbt_to_dict(value)
        elif isinstance(value, TAG_List):
            as_dict[key] = [convert_nbt_to_dict(list_value) for list_value in value]
        elif isinstance(value, (TAG_String, TAG_Int, TAG_Long, TAG_Byte)):
            as_dict[key] = value.value
        else:
            as_dict[key] = value
    return as_dict


def yaml_load(path: Path, config_name: str = "config.yaml") -> dict:
    """Load a yaml file as a dict."""
    config = path.joinpath(config_name)
    if not config.exists():
        raise Exception(config_name)
    return yaml.safe_load(open(config, "r"))


def get_modules(path: Path) -> Iterable[Module]:
    """Get all modules in the modules folder recursively."""
    for module in path.rglob("*.py"):
        yield Module(base_path=path.parent, path=module)


async def get_mc_player(
    database, session: ClientSession, player_id: str
) -> MinecraftPlayer:
    """Get a player from the api."""
    player = await db.players.get_player(database, player_id)
    if player is None or datetime.fromisoformat(
        player["last_updated"]
    ) < datetime.now() - timedelta(days=1):
        async with session.get(
            f"https://sessionserver.mojang.com/session/minecraft/profile/{player_id}"
        ) as request:
            response = await request.json()
            await db.players.insert_player(
                database,
                player_id,
                response["name"],
            )
    player = await db.players.get_player(database, player_id)
    return MinecraftPlayer(**player)