import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from discord import Locale, app_commands
from pydantic import BaseModel, root_validator
from json import load
from utils.converters import get_uuid_from_parts


class Object:
    ...


class DevilFruit(BaseModel):
    name: str
    format_name: str
    qualified_name: str
    rarity: str


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
    discord_id: Optional[int]
    name: str
    crew: Optional[str]
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
        return ".".join(
            str(self.path.relative_to(self.base_path)).split(os.sep)
        ).replace(".py", "")


class Translator(app_commands.Translator):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    async def load(self):
        self.translations = {}
        locales_path = Path("resources/locales")
        for locale in Locale:
            locale_path = locales_path.joinpath(
                locale.name + "." + locale.value + ".json"
            )
            if locale_path.exists():
                self.translations[locale] = load(locale_path.open())
            else:
                self.translations[locale] = {}

    async def unload(self):
        ...

    async def translate(
        self, string: app_commands.locale_str, locale: Locale, _
    ) -> Optional[str]:
        return self.translations[locale].get(
            string,
            self.translations[getattr(Locale, self.bot.config.language)].get(
                string, None
            ),
        )

    async def run(self, string: app_commands.locale_str, locale: Locale):
        return await self.translate(string, locale, None)
