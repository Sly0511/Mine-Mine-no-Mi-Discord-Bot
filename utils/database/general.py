import asqlite


async def build(database_path):
    async with asqlite.connect(database_path) as db:
        async with db.cursor() as c:
            with open("utils/database/build.sql", "r") as f:
                await c.executescript(f.read())
                print("Ensured database schema.")
