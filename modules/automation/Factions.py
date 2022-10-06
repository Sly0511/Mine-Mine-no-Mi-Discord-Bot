from discord.ext import commands
from utils.objects import PlayerData


class Factions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener("on_player_data")
    async def update_player_data(self, player_data: list[PlayerData]):
        """Updates the devil fruit circulation."""
        await self.bot.modules_ready.wait()
        guild = self.bot.get_guild(1014333541213024328)
        roles = {
            name: guild.get_role(role_id)
            for name, role_id in [
                ["Pirate", 1014373641254879253],
                ["Marine", 1014373640466341938],
                ["Revolutionary", 1014373639421960283],
                ["BountyHunter", 1014373638776029185],
            ]
        }
        for player in player_data:
            if player.discord_id is None:
                continue
            member = guild.get_member(player.discord_id)
            if not member:
                continue
            role = None
            if player.faction:
                role = roles.get(player.faction.name)
            if role and role not in member.roles:
                await member.add_roles(role)
            for not_role in roles.values():
                if role != not_role and not_role in member.roles:
                    await member.remove_roles(not_role)


async def setup(bot):
    await bot.add_cog(Factions(bot))
