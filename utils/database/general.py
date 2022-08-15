async def build(database):
    async with database.cursor() as c:
        with open("utils/database/build.sql", "r") as f:
            await c.executescript(f.read())
            print("Ensured database schema.")
