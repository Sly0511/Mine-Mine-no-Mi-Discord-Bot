from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Iterable, Union

import yaml
from aiohttp import ClientSession
from ftputil import FTPHost
from nbt import nbt
from nbt.nbt import TAG_Byte, TAG_Compound, TAG_Double, TAG_Float, TAG_Int, TAG_List, TAG_Long, TAG_String

from utils.configs import FTPConfig
from utils.FTPImpl import FTPServer
from utils.objects import MinecraftPlayer, Module
from utils.database.models import Players


def chunks(l: Iterable, n: int) -> Iterable:
    """Yield successive n-sized chunks from list."""
    for i in range(0, len(l), n):
        yield l[i : i + n]


def convert_nbt_to_dict(data: nbt.NBTFile) -> dict:
    """Convert nbt file to dict."""
    if isinstance(data, (TAG_String, TAG_Int, TAG_Long, TAG_Byte, TAG_Float, TAG_Double)):
        return data.value
    as_dict = {}
    for key, value in data.iteritems():
        if isinstance(value, TAG_Compound):
            as_dict[key] = convert_nbt_to_dict(value)
        elif isinstance(value, TAG_List):
            as_dict[key] = [convert_nbt_to_dict(list_value) for list_value in value]
        elif isinstance(value, (TAG_String, TAG_Int, TAG_Long, TAG_Byte, TAG_Float, TAG_Double)):
            as_dict[key] = value.value
        else:
            as_dict[key] = None
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


async def get_mc_player(session: ClientSession, player_id: str) -> MinecraftPlayer:
    """Get a player from the api."""
    player = await Players.find_one(Players.uuid == player_id)
    if player is None or datetime.utcfromtimestamp(player.last_updated) < datetime.now() - timedelta(days=1):
        async with session.get(f"https://sessionserver.mojang.com/session/minecraft/profile/{player_id}") as request:
            response = await request.json()
            if player is None:
                player = Players(uuid=player_id, name=response["name"], last_updated=int(datetime.utcnow().timestamp()))
            else:
                player.name = response["name"]
            await player.save()
    return MinecraftPlayer(
        uuid=player.uuid, name=player.name, discord_id=player.discord_id, last_updated=player.last_updated
    )


def read_ftp_file(server: FTPHost, path: Path):
    """Read a file from the ftp server."""
    if not server.path.exists(path):
        raise Exception(f"File {path} does not exist in the Server.")
    with server.open(path, "rb") as f:
        return BytesIO(f.read())


def download_ftp_file(server: Union[FTPHost, FTPConfig], path: str, destination: Path, mode="rb"):
    """Read a file from the ftp server."""
    close = False
    if isinstance(server, FTPConfig):
        server = FTPServer(server).connect()
        close = True
    if not server.path.exists(path):
        raise Exception(f"File {path} does not exist in the Server.")
    if not destination.parent.exists():
        destination.parent.mkdir(parents=True)
    server.download_if_newer(path, destination)
    if close:
        server.close()
    return open(destination, "rb").read()
