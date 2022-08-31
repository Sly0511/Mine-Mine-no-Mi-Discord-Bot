from discord.ext import commands
from datetime import timedelta
from discord import AllowedMentions, Object


class Tired(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener("on_message")
    async def stop_fucking_pinging(self, message):
        if not message.guild:
            return
        bl = [
            565097923025567755,  # Sly
        ]
        bl_members = [message.guild.get_member(i) for i in bl]
        if pinged := [admin.mention for admin in bl_members if admin in message.mentions]:
            try:
                await message.author.timeout(timedelta(minutes=5), reason="I said to stop fucking pinging.")
                await message.reply(
                    f"Stop pinging {','.join(pinged)}!"
                    + ("\nDisable reply mentions asshole." if message.reference else ""),
                    delete_after=10,
                    allowed_mentions=AllowedMentions.none(),
                )
            except:
                pass
        if message.stickers:
            try:
                await message.delete()
            except:
                pass
        if message.channel.id == 996852283180597268:
            already_sent = []
            async for m in message.channel.history(limit=1000, after=Object(id=996858782317543514), oldest_first=False):
                if m.author.id in already_sent:
                    await m.delete()
                    continue
                already_sent.append(m.author.id)


async def setup(bot):
    await bot.add_cog(Tired(bot))
