from datetime import datetime


async def get_players(database):
    async with database.cursor() as c:
        await c.execute("SELECT * FROM Players")
        return await c.fetchall()

async def get_players_with_crews(database):
    async with database.cursor() as c:
        await c.execute("SELECT * FROM Players WHERE crew_name IS NOT NULL")
        return await c.fetchall()


async def insert_player(database, player_id: str, name: str):
    async with database.cursor() as c:
        await c.execute(
            "INSERT INTO Players (uuid, name, last_updated) VALUES (?, ?, ?)",
            (player_id, name, datetime.utcnow()),
        )
        await database.commit()


async def update_player_name(database, player_id: str, name: str):
    async with database.cursor() as c:
        await c.execute(
            "UPDATE Players SET name = ? AND last_updated = ? WHERE uuid = ?",
            (name, datetime.utcnow(), player_id),
        )
        await database.commit()


async def get_player(database, player_id: str):
    async with database.cursor() as c:
        await c.execute("SELECT * FROM Players WHERE uuid = ?", (player_id,))
        return await c.fetchone()


async def get_player_by_name(database, name: str):
    async with database.cursor() as c:
        await c.execute("SELECT * FROM Players WHERE name = ?", (name,))
        return await c.fetchone()


async def get_player_by_discord_id(database, discord_id: int):
    async with database.cursor() as c:
        await c.execute("SELECT * FROM Players WHERE discord_id = ?", (discord_id,))
        return await c.fetchone()
