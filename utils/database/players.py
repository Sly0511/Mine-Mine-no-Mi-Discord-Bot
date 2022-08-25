from datetime import datetime
import asqlite


async def get_players(database_path):
    async with asqlite.connect(database_path) as db:
        async with db.cursor() as c:
            await c.execute("SELECT * FROM Players")
            return await c.fetchall()


async def get_players_with_crews(database_path):
    async with asqlite.connect(database_path) as db:
        async with db.cursor() as c:
            await c.execute("SELECT * FROM Players WHERE crew_name IS NOT NULL")
            return await c.fetchall()


async def insert_player(database_path, player_id: str, name: str):
    async with asqlite.connect(database_path) as db:
        async with db.cursor() as c:
            await c.execute(
                "INSERT OR REPLACE INTO Players (uuid, name, last_updated) VALUES (?, ?, ?)",
                (player_id, name, datetime.utcnow()),
            )
            await db.commit()


async def update_player_name(database_path, player_id: str, name: str):
    async with asqlite.connect(database_path) as db:
        async with db.cursor() as c:
            await c.execute(
                "UPDATE Players SET name = ? AND last_updated = ? WHERE uuid = ?",
                (name, datetime.utcnow(), player_id),
            )
            await db.commit()


async def update_player_discord_id(database_path, player_id: str, discord_id: int):
    async with asqlite.connect(database_path) as db:
        async with db.cursor() as c:
            await c.execute(
                "UPDATE Players SET discord_id = ?, last_updated = ? WHERE uuid = ?",
                (discord_id, datetime.utcnow(), player_id),
            )
            await db.commit()


async def get_player(database_path, player_id: str):
    async with asqlite.connect(database_path) as db:
        async with db.cursor() as c:
            await c.execute("SELECT * FROM Players WHERE uuid = ?", (player_id,))
            return await c.fetchone()


async def get_player_by_name(database_path, name: str):
    async with asqlite.connect(database_path) as db:
        async with db.cursor() as c:
            await c.execute("SELECT * FROM Players WHERE name = ?", (name,))
            return await c.fetchone()


async def get_player_by_discord_id(database_path, discord_id: int):
    async with asqlite.connect(database_path) as db:
        async with db.cursor() as c:
            await c.execute("SELECT * FROM Players WHERE discord_id = ?", (discord_id,))
            return await c.fetchone()
