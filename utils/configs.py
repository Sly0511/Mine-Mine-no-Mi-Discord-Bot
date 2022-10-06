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
    linux_user: str
    server_name: str
    server_ip: str
    server_port: int
    server_path: Path
    world_name: str
    modpack_download: str
    rcon_ip: str
    rcon_port: int
    rcon_password: str
    discord_api_key: str
    discord_server_id: int
    bot_owners: list[int] = []
    bot_admins: list[int] = []
    staff_role: int
    patreon_role: int
    link_role: int
    devil_fruits: DevilFruitConfig
    ftp: FTPConfig
