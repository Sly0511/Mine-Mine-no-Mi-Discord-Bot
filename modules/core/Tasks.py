from io import BytesIO

from discord.ext import commands, tasks
from nbt import nbt
from utils.functions import convert_nbt_to_dict


class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.nbt_path = self.bot.config.server_path.joinpath(
            "{0}/data/mineminenomi.dat".format(self.bot.config.world_name)
        )

    async def cog_load(self):
        self.read_mmnm_nbt.start()

    async def cog_unload(self):
        self.read_mmnm_nbt.cancel()

    @tasks.loop(minutes=5)
    async def read_mmnm_nbt(self):
        """Reads the mineminenomi.dat file every 5 minutes."""
        await self.bot.modules_ready.wait()
        # _file = open(self.nbt_path, "rb").read()
        _file = open("mineminenomi.dat", "rb").read()
        nbt_data = nbt.NBTFile(fileobj=BytesIO(_file))
        nbt_dict = convert_nbt_to_dict(nbt_data)
        self.bot.dispatch("mmnm_nbt_read", nbt_dict)


async def setup(bot):
    await bot.add_cog(Tasks(bot))
