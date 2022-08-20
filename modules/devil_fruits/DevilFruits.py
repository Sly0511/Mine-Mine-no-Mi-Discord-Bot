from datetime import datetime
from json import load
import json

from discord import Embed, app_commands
from discord.errors import NotFound
from discord.ext import commands
from discord.utils import get
from utils.functions import chunks
from utils.objects import DevilFruit, PlayerData


class devil_fruit_circulation(commands.Cog):
    """A module for Devil Fruit Circulation."""

    def __init__(self, bot):
        self.bot = bot
        self.config = self.bot.config.devil_fruits
        self.fruits = list(self.list_devil_fruits(load(open("resources/fruits.json"))))
        self.players = []

    async def get_editable_message(self, channel):
        """Gets a message that can be edited from the specified channel."""
        if channel is None:
            raise Exception(
                "\nUnable to start updating devil fruit circulation, no channel found with ID {0}\n"
                "Make sure to edit '\modules\devil_fruit_circulation\config.yaml'".format(self.config.channel)
            )
        async for m in channel.history(limit=50):
            if (
                m.author == self.bot.user
                and m.embeds
                and m.embeds[0].description == "__**All available Devil Fruits**__"
            ):
                return m
        return None

    @commands.Cog.listener("on_player_data")
    async def update_df_circulation(self, player_data: list[PlayerData]):
        """Updates the devil fruit circulation."""
        await self.bot.modules_ready.wait()
        self.players = player_data
        devil_fruits = [fruit for player in player_data for fruit in player.devil_fruits]
        channel = self.bot.get_channel(self.config.channel)
        update = self.build_formatted_message(devil_fruits)
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

    def build_formatted_message(self, unavailable_fruits: list[DevilFruit]) -> Embed:
        """Builds the formatted message to be sent to the channel."""
        emojis = {
            "golden_box_emoji": self.bot.get_emoji(self.config.golden_box),
            "iron_box_emoji": self.bot.get_emoji(self.config.iron_box),
            "wooden_box_emoji": self.bot.get_emoji(self.config.wooden_box),
        }
        embed: Embed = Embed(
            title="{g}{i}{w}Available Devil Fruits {w}{i}{g}".format(
                g=emojis["golden_box_emoji"],
                i=emojis["iron_box_emoji"],
                w=emojis["wooden_box_emoji"],
            ),
            description="__**All available Devil Fruits**__",
            color=self.bot.GOLDEN_COLOR,
            timestamp=datetime.utcnow(),
        )
        embed.set_footer(text="Updates every 5 minutes | Last updated")
        order = ["golden_box", "iron_box", "wooden_box"]
        available_fruits = [
            f"{emojis.get(fruit.rarity+'_emoji')}{fruit.format_name}"
            for fruit in sorted(self.fruits, key=lambda x: (order.index(x.rarity), x.format_name))
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
                    yield DevilFruit(rarity=rarity, qualified_name=qualified_name, **devil_fruit)

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

    @app_commands.command(name="check_fruit", description="Get information about who owns a devil fruit.")
    async def devilfruit(self, interaction, fruit_name: str):
        """Gets information about a devil fruit."""
        fruit = get(self.fruits, qualified_name=fruit_name)
        embed = Embed(description=f"**{fruit.format_name}** Devil Fruit Owners")
        for player in self.players:
            if fruit in player.devil_fruits:
                embed.add_field(
                    name=player.name,
                    value=f"Eaten: "
                    + ("Yes" if fruit in player.eaten_devil_fruits else "No")
                    + "\n"
                    + "Inventory: "
                    + (
                        str(player.inventory_devil_fruits.count(fruit))
                        if fruit in player.inventory_devil_fruits
                        else "No"
                    ),
                    inline=True,
                )
        if not embed.fields:
            embed.description += "\n\nNo one owns this Devil Fruit."
        await interaction.response.send_message(embed=embed)

    @devilfruit.autocomplete("fruit_name")
    async def devilfruit_autocomplete(self, interaction, current: str):
        """Autocomplete for devilfruit command."""
        fruits = list(filter(lambda x: x.format_name.lower().startswith(current.lower()), self.fruits))
        return [
            app_commands.Choice(name=fruit.format_name, value=fruit.qualified_name)
            for fruit in sorted(fruits, key=lambda x: x.format_name)
        ][:25]

    @app_commands.command(name="duplicate_df", description="List Devil Fruit dupes.")
    async def get_duplicates(self, interaction):
        """List Devil Fruit dupes."""
        fruits_list = {}
        for fruit in self.fruits:
            for player in self.players:
                if fruit in player.devil_fruits:
                    if fruit.format_name not in fruits_list:
                        fruits_list[fruit.format_name] = []
                    fruits_list[fruit.format_name].append([player.name, player.uuid])

        await interaction.response.send_message(
            f"""```\n{json.dumps({k: v for k, v in fruits_list.items() if len(v) > 1}, indent=4)}\n```"""
        )

    @app_commands.command(name="too_many_df", description="List Devil Fruit in inventory over 1.")
    async def too_many_df(self, interaction):
        """List Devil Fruit dupes."""
        fruits_list = {}
        for player in self.players:
            if len(player.inventory_devil_fruits) > 1:
                fruits_list[player.name].extend([f.format_name for f in player.inventory_devil_fruits])

        await interaction.response.send_message(
            f"""```\n{json.dumps({k: v for k, v in fruits_list.items() if len(v) > 1}, indent=4)}\n```"""
        )


async def setup(bot):
    await bot.add_cog(devil_fruit_circulation(bot))
