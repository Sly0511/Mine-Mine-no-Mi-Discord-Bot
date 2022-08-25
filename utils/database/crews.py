import asqlite


async def get_crews(database_path):
    async with asqlite.connect(database_path) as db:
        async with db.cursor() as c:
            await c.execute("SELECT * FROM Crews")
            return await c.fetchall()


async def get_crew(database_path, name: str):
    async with asqlite.connect(database_path) as db:
        async with db.cursor() as c:
            await c.execute("SELECT * FROM Crews WHERE name = ?", (name,))
            return await c.fetchone()


async def add_crew(database_path, name: str, captain_uuid: str):
    async with asqlite.connect(database_path) as db:
        async with db.cursor() as c:
            await c.execute(
                "INSERT INTO Crews (name, captain_uuid) VALUES (?, ?)",
                (name, captain_uuid),
            )
            await db.commit()


async def update_captain(database_path, crew_name: int, player_id: str):
    async with asqlite.connect(database_path) as db:
        async with db.cursor() as c:
            await c.execute("UPDATE Crews SET captain_uuid = ? WHERE name = ?", (player_id, crew_name))
            await db.commit()


async def update_role_id(database_path, crew_name: int, role_id: int):
    async with asqlite.connect(database_path) as db:
        async with db.cursor() as c:
            await c.execute("UPDATE Crews SET role_id = ? WHERE name = ?", (role_id, crew_name))
            await db.commit()
