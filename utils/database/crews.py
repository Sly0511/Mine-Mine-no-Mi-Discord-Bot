async def get_crews(database):
    async with database.cursor() as c:
        await c.execute("SELECT * FROM Crews")
        return await c.fetchall()


async def get_crew(database, name: str):
    async with database.cursor() as c:
        await c.execute("SELECT * FROM Crews WHERE name = ?", (name,))
        return await c.fetchone()


async def add_crew(database, name: str, captain_uuid: str):
    async with database.cursor() as c:
        await c.execute(
            "INSERT INTO Crews (name, captain_uuid) VALUES (?, ?)",
            (name, captain_uuid),
        )
        await database.commit()


async def update_captain(database, crew_name: int, player_id: str):
    async with database.cursor() as c:
        await c.execute(
            "UPDATE Crews SET captain_uuid = ? WHERE name = ?", (player_id, crew_name)
        )
        await database.commit()


async def update_role_id(database, crew_name: int, role_id: int):
    async with database.cursor() as c:
        await c.execute(
            "UPDATE Crews SET role_id = ? WHERE name = ?", (role_id, crew_name)
        )
        await database.commit()
