from discord.ext import commands


class AdminDevilFruits(commands.Cog):
    ...


async def setup(bot):
    await bot.add_cog(AdminDevilFruits(bot))
