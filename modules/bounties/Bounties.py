from discord import Embed
from discord.ext import commands
from utils.objects import PlayerData, Factions


class Bounties(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.players = []

    @commands.Cog.listener("on_player_data")
    async def update_bounties(self, player_data: list[PlayerData]):

        await self.bot.modules_ready.wait()
        self.players = player_data

    @commands.hybrid_command(name="bounties", description="Lists all the bounties.")
    async def bounties(self, ctx):
        e = Embed(title="Bounties", description="```\n")
        for player in filter(
            lambda x: x.bounty > 1000,
            sorted(self.players, key=lambda x: x.bounty, reverse=True),
        ):
            e.description += "{:<7} - {}\n".format(player.bounty, player.name)
        e.description += "```"
        await ctx.send(embed=e)

    @commands.hybrid_command(name="doriki", description="Lists all the doriki.")
    async def doriki(self, ctx):
        e = Embed(title="Doriki", description="```\n")
        for player in filter(
            lambda x: x.doriki > 2000,
            sorted(self.players, key=lambda x: x.doriki, reverse=True),
        ):
            e.description += "{:<5} - {}\n".format(player.doriki, player.name)
        e.description += "```"
        await ctx.send(embed=e)

    @commands.hybrid_command(name="loyalty", description="Lists all the loyalty.")
    async def loyalty(self, ctx):
        e = Embed(title="Loyalty", description="```\n")
        for player in filter(
            lambda x: x.faction == Factions.Marine,
            sorted(self.players, key=lambda x: x.loyalty, reverse=True),
        ):
            e.description += "{:<4} - {}\n".format(player.loyalty, player.name)
        e.description += "```"
        await ctx.send(embed=e)

    @commands.hybrid_command(name="belly", description="Lists all the belly.")
    async def belly(self, ctx):
        e = Embed(title="Belly", description="```\n")
        for player in filter(
            lambda x: x.belly > 1000,
            sorted(self.players, key=lambda x: x.belly, reverse=True),
        ):
            e.description += "{:<7} - {}\n".format(player.belly, player.name)
        e.description += "```"
        await ctx.send(embed=e)

    @commands.hybrid_command(name="hardening", description="Lists all the hardening Haki.")
    async def harderning_haki(self, ctx):
        e = Embed(title="Hardening Haki", description="```\n")
        for player in filter(
            lambda x: x.harderning_haki > 0,
            sorted(self.players, key=lambda x: x.harderning_haki, reverse=True),
        ):
            e.description += "{:<4} - {}\n".format(player.harderning_haki, player.name)
        e.description += "```"
        await ctx.send(embed=e)

    @commands.hybrid_command(name="imbuing", description="Lists all the imbuing Haki.")
    async def imbuing_haki(self, ctx):
        e = Embed(title="Imbuing Haki", description="```\n")
        for player in filter(
            lambda x: x.imbuing_haki > 0,
            sorted(self.players, key=lambda x: x.imbuing_haki, reverse=True),
        ):
            e.description += "{:<4} - {}\n".format(player.imbuing_haki, player.name)
        e.description += "```"
        await ctx.send(embed=e)

    @commands.hybrid_command(name="observation", description="Lists all the observation Haki.")
    async def observation_haki(self, ctx):
        e = Embed(title="Observation Haki", description="```\n")
        for player in filter(
            lambda x: x.observation_haki > 0,
            sorted(self.players, key=lambda x: x.observation_haki, reverse=True),
        ):
            e.description += "{:<4} - {}\n".format(player.observation_haki, player.name)
        e.description += "```"
        await ctx.send(embed=e)

    @commands.hybrid_command(name="conqueror", description="Lists all the conqueror Haki.")
    async def conqueror_haki(self, ctx):
        e = Embed(title="Conquerors Haki", description="```\n")
        for player in filter(
            lambda x: x.haoshoku_haki > 0,
            sorted(self.players, key=lambda x: x.haoshoku_haki, reverse=True),
        ):
            e.description += "{}\n".format(player.name)
        e.description += "```"
        await ctx.send(embed=e)


async def setup(bot):
    await bot.add_cog(Bounties(bot))
