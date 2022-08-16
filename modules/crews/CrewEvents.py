from discord.ext import commands
from utils import database as db
from discord.utils import get
from utils.objects import Crew


class CrewEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener("on_mmnm_nbt_read")
    async def read_nbt_data(self, nbt: dict):
        crews = db.crews.get_crews(self.bot.db)
        for crew_data in nbt["data"]["crews"]:
            if get(crews, name=crew_data["name"]) is None:
                self.bot.dispatch("crew_created", Crew(**crew_data))
        for crew in crews:
            if get(nbt["data"]["crews"], name=crew.name) is None:
                self.bot.dispatch("crew_deleted", Crew(**crew))
        for crew_data in nbt["data"]["crews"]:
            crew = Crew(**crew_data)
            for member in crew.members:
                ...

    @commands.Cog.listener("on_crew_created")
    async def create_crew(self, crew: Crew):
        await db.crews.create_crew(self.bot.db, crew.name, crew.captain_uuid)
        for member in crew.members:
            ...

    @commands.Cog.listener("on_crew_deleted")
    async def delete_crew(self, crew: Crew):
        await db.crews.delete_crew(self.bot.db, crew.name)
        for member in crew.members:
            ...


async def setup(bot):
    await bot.add_cog(CrewEvents(bot))
