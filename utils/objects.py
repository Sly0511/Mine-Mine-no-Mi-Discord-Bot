import os
from typing import Optional
from pydantic import BaseModel
from pathlib import Path
from datetime import datetime


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


class Crew(BaseModel):
    name: str
    members: list[CrewMember]
    jollyRoger: dict


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
