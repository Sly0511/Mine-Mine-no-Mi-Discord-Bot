from datetime import datetime
from json import load

from discord import Embed
from discord.errors import NotFound
from discord.ext import commands
from discord.utils import get
from utils.functions import chunks
from utils.objects import DevilFruit


class devil_fruit_circulation(commands.Cog):
    """A module for Devil Fruit Circulation."""

    def __init__(self, bot):
        self.bot = bot
        self.config = self.bot.config.devil_fruits
        self.fruits = list(self.list_devil_fruits(load(open("resources/fruits.json"))))

    async def get_editable_message(self, channel):
        """Gets a message that can be edited from the specified channel."""
        if channel is None:
            raise Exception(
                "\nUnable to start updating devil fruit circulation, no channel found with ID {0}\n"
                "Make sure to edit '\modules\devil_fruit_circulation\config.yaml'".format(
                    self.config.channel
                )
            )
        async for m in channel.history(limit=50):
            if (
                m.author == self.bot.user
                and m.embeds
                and m.embeds[0].description == "__**All available Devil Fruits**__"
            ):
                return m
        return None

    @commands.Cog.listener("on_mmnm_nbt_read")
    async def update_df_circulation(self, nbt_data: dict):
        """Updates the devil fruit circulation."""
        await self.bot.modules_ready.wait()
        channel = self.bot.get_channel(self.config.channel)
        update = self.build_formatted_message(nbt_data)
        if not hasattr(self, "df_message"):
            try:
                self.df_message = await self.get_editable_message(channel)
            except Exception as e:
                print(e)
                return
        if self.df_message is None:
            self.df_message = await channel.send(embed=update)
        else:
            try:
                await self.df_message.edit(embed=update)
            except NotFound:
                self.df_message = await channel.send(embed=update)
        await self.df_message.edit(embed=update)

    def build_formatted_message(self, fruit_data: dict) -> Embed:
        """Builds the formatted message to be sent to the channel."""
        emojis = {
            "golden_box_emoji": self.bot.get_emoji(self.config.golden_box),
            "iron_box_emoji": self.bot.get_emoji(self.config.iron_box),
            "wooden_box_emoji": self.bot.get_emoji(self.config.wooden_box),
        }
        embed: Embed = Embed(
            title="{g}{i}{w}Current Devilfruit Circulation{w}{i}{g}".format(
                g=emojis["golden_box_emoji"],
                i=emojis["iron_box_emoji"],
                w=emojis["wooden_box_emoji"],
            ),
            description="__**All available Devil Fruits**__",
            color=self.bot.GOLDEN_COLOR,
            timestamp=datetime.utcnow(),
        )
        embed.set_footer(text="Circulation is updated every 5 minutes | Last updated")
        eaten_fruits = self.list_eaten_fruits(self.fruits, fruit_data)
        inventory_fruits = self.list_inventory_fruits(self.fruits, fruit_data)
        unavailable_fruits = eaten_fruits + inventory_fruits
        order = ["golden_box", "iron_box", "wooden_box"]
        available_fruits = [
            f"{emojis.get(fruit.rarity+'_emoji')}{fruit.format_name}"
            for fruit in sorted(self.fruits, key=lambda x: order.index(x.rarity))
            if fruit not in unavailable_fruits
        ]
        available_fruits_fields = chunks(available_fruits, 8)
        for fruits in available_fruits_fields:
            embed.add_field(
                name="\u200b",
                value="\n".join(fruits),
            )
        return embed

    def list_devil_fruits(self, data: dict):
        """List all devil fruits."""
        for rarity, fruits in data.items():
            for fruit in fruits:
                for qualified_name, devil_fruit in fruit.items():
                    yield DevilFruit(
                        rarity=rarity, qualified_name=qualified_name, **devil_fruit
                    )

    def list_golden_devil_fruits(self, data: list[DevilFruit]):
        """List all golden box devil fruits."""
        return list(filter(lambda x: x.rarity == "golden_box", data))

    def list_iron_devil_fruits(self, data: list[DevilFruit]):
        """List all iron box devil fruits."""
        return list(filter(lambda x: x.rarity == "iron_box", data))

    def list_wooden_devil_fruits(self, data: list[DevilFruit]):
        """List all wooden box devil fruits."""
        return list(filter(lambda x: x.rarity == "wooden_box", data))

    def list_eaten_fruits(self, data: list[DevilFruit], nbt_data: dict):
        """List all devil fruits eaten by players."""
        eaten_fruits = nbt_data["data"].get("ateDevilFruits")
        if eaten_fruits is None:
            return []
        return list(
            filter(
                lambda x: x.qualified_name in eaten_fruits.values(),
                data,
            )
        )

    def list_inventory_fruits(self, data: list[DevilFruit], nbt_data: dict):
        """List all devil fruits in inventories."""
        inventory_fruits = nbt_data["data"].get("devilFruitsInInventories", [])
        fruits = []
        for inventory in inventory_fruits:
            for i in range(inventory.get("fruits")):
                if fruit_name := inventory.get(f"fruit-{i}"):
                    fruits.append(get(data, qualified_name=fruit_name))
        return fruits


async def setup(bot):
    await bot.add_cog(devil_fruit_circulation(bot))
