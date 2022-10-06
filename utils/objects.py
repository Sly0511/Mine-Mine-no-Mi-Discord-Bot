import asyncio
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from enum import Enum

from discord import Locale, app_commands
from pydantic import BaseModel, root_validator
from json import load
from utils.converters import get_uuid_from_parts
from utils.configs import FTPConfig
from aioftp import Client
from io import BytesIO


class Object:
    ...


class FTPServer:
    def __init__(self, ftp_config: FTPConfig):
        self.ftp = ftp_config

    async def download_player_data(self, path):
        cache = Path("cache/player_data")
        async with Client.context(self.ftp.host, self.ftp.port, self.ftp.username, self.ftp.password) as client:
            for path, info in await client.list(path):
                if info["type"] == "file" and path.suffix == ".dat":
                    last_modified = datetime.strptime(info["modify"], "%Y%m%d%H%M%S")
                    cached_file = cache.joinpath(path.name)
                    if (
                        not cached_file.exists()
                        or last_modified > datetime.utcnow() - timedelta(minutes=10)
                        or info["size"] != cached_file.stat().st_size
                    ):
                        await client.download(path, cached_file, write_into=True)

    async def get_file(self, path):
        async with Client.context(self.ftp.host, self.ftp.port, self.ftp.username, self.ftp.password) as client:
            raw_data = await client.download_stream(path)
            return await raw_data.read()


class Races(Enum):
    Human = "human"
    Cyborg = "cyborg"
    Mink = "mink"
    Fishman = "fishman"


class subRaces(Enum):
    Bunny = "mink_bunny"
    Dog = "mink_dog"
    Lion = "mink_lion"


class Factions(Enum):
    Pirate = "pirate"
    Marine = "marine"
    Revolutionary = "revolutionary"
    BountyHunter = "bounty_hunter"


class FightingStyles(Enum):
    Brawler = "brawler"
    Swordsman = "swordsman"
    BlackLeg = "black_leg"
    Sniper = "sniper"
    Doctor = "doctor"
    ArtofWeather = "art_of_weather"


class DevilFruit(BaseModel):
    name: str
    format_name: str
    qualified_name: str
    rarity: str


class PlayerData(BaseModel):
    uuid: str
    name: str
    race: Optional[Races]
    sub_race: Optional[subRaces]
    faction: Optional[Factions]
    fighting_style: Optional[FightingStyles]
    inventory: list[dict]
    devil_fruits: list[DevilFruit]
    eaten_devil_fruits: list[DevilFruit]
    inventory_devil_fruits: list[DevilFruit]
    belly: int
    bounty: int
    loyalty: int
    doriki: int
    harderning_haki: float
    imbuing_haki: float
    observation_haki: float
    haoshoku_haki: bool
    haki_limit: float
    mob_kills: dict
    discord_id: Optional[int]
    last_seen: datetime
    inactive: bool


class CrewMember(BaseModel):
    username: str
    isCaptain: bool
    idMost: int
    idLeast: int
    uuid: Optional[str] = None

    @root_validator(pre=True)
    def get_uuid(cls, values: dict):
        values["uuid"] = get_uuid_from_parts(values["idMost"], values["idLeast"])
        return values


class Crew(BaseModel):
    name: str
    members: list[CrewMember]
    jollyRoger: dict

    @root_validator(pre=True)
    def get_captain_uuid(cls, values: dict):
        for member in values["members"]:
            if member.isCaptain:
                values["captain_uuid"] = member.uuid
                break
        return values


class MinecraftPlayer(BaseModel):
    uuid: str
    name: str
    discord_id: Optional[int]
    last_updated: datetime


class Bounty(BaseModel):
    player: MinecraftPlayer
    amount: int


class Module(BaseModel):
    base_path: Path
    path: Path

    @property
    def name(self) -> str:
        return self.path.stem

    @property
    def qualified_name(self) -> str:
        return self.path.name

    @property
    def relative_path(self) -> Path:
        return self.path.relative_to(Path.cwd())

    @property
    def spec(self) -> str:
        return ".".join(str(self.path.relative_to(self.base_path)).split(os.sep)).replace(".py", "")


class Translator(app_commands.Translator):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    async def load(self):
        self.translations = {}
        locales_path = Path("resources/locales")
        for locale in Locale:
            locale_path = locales_path.joinpath(locale.name + "." + locale.value + ".json")
            if locale_path.exists():
                self.translations[locale] = load(locale_path.open())
            else:
                self.translations[locale] = {}

    async def unload(self):
        ...

    async def translate(self, string: app_commands.locale_str, locale: Locale, _) -> Optional[str]:
        return self.translations[locale].get(
            string,
            self.translations[getattr(Locale, self.bot.config.language)].get(string, None),
        )

    async def run(self, string: app_commands.locale_str, locale: Locale):
        return await self.translate(string, locale, None)
