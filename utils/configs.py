from pydantic import BaseModel
from pathlib import Path


class DevilFruitConfig(BaseModel):
    channel: int
    golden_box: int
    iron_box: int
    wooden_box: int


class FTPConfig(BaseModel):
    host: str
    username: str
    password: str
    port: int


class BotConfig(BaseModel):
    language: str
    server_path: Path
    world_name: str
    discord_api_key: str
    discord_server_id: int
    bot_owners: list[int] = []
    devil_fruits: DevilFruitConfig
    ftp: FTPConfig
