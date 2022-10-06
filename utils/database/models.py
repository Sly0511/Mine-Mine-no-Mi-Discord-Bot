from datetime import datetime
from typing import Optional

from beanie import Document, Indexed, Insert, Replace, before_event, after_event, PydanticObjectId
from pydantic import BaseModel


class Players(Document):
    uuid: Indexed(str, unique=True)
    name: Indexed(str, unique=True)
    discord_id: Optional[Indexed(int)] = None
    last_updated: int = None

    @before_event(Insert)
    def get_time(self):
        self.last_updated = int(datetime.utcnow().timestamp())


class Cooldowns(BaseModel):
    race_blood_change: int = 0


class Economy(BaseModel):
    balance: int = 0
    boost_count: int = 0


class Users(Document):
    discord_id: Indexed(int, unique=True)
    race: Optional[str] = None
    bloodline: Optional[str] = None
    inventory: list = []
    economy: Economy = Economy()
    cooldowns: Cooldowns = Cooldowns()
