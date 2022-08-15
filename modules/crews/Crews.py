import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import get
from utils.objects import Crew


class Crews(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mmnm_crews = []

    @commands.Cog.listener("on_mmnm_nbt_read")
    async def update_nbt_data(self, nbt: dict):
        self.mmnm_crews = sorted(
            [Crew(**crew) for crew in nbt["data"]["crews"]],
            key=lambda x: x.name,
        )

    @commands.hybrid_command(name="crews", description="Lists all the crews.")
    async def crews(self, ctx, *, name: str = None):
        crew = get(self.mmnm_crews, name=name)
        await ctx.send(crew.name, ephemeral=True)

    @crews.autocomplete(name="name")
    async def crews_name_autocomplete(
        self, interaction: discord.Interaction, current: str
    ):
        crews = filter(lambda x: current.lower() in x.name.lower(), self.mmnm_crews)
        return [app_commands.Choice(name=x.name, value=x.name) for x in crews][:25]


async def setup(bot):
    await bot.add_cog(Crews(bot))
