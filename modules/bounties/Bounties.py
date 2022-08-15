from discord import Embed
from discord.ext import commands
from utils.functions import get_mc_player
from utils.objects import Bounty


class Bounties(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bounties = []

    @commands.Cog.listener("on_mmnm_nbt_read")
    async def update_nbt_data(self, nbt: dict):
        self.bounties.clear()
        for uuid, value in nbt["data"]["issuedBounties"].items():
            player = await get_mc_player(self.bot.db, self.bot.constants.RSession, uuid)
            self.bounties.append(Bounty(player=player, amount=value))
        self.bounties.sort(key=lambda x: x.amount, reverse=True)

    @commands.hybrid_command(name="bounties", description="Lists all the bounties.")
    async def bounties(self, ctx):
        e = Embed(title="Bounties", description="```\n")
        for bounty in filter(lambda x: x.amount > 0, self.bounties):
            e.description += "{:<7} - {}\n".format(bounty.amount, bounty.player.name)
        e.description += "```"
        await ctx.send(embed=e)


async def setup(bot):
    await bot.add_cog(Bounties(bot))
