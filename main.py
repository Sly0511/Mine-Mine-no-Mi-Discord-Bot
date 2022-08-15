import asyncio
from pathlib import Path

import asqlite
import discord
import yaml
from aiohttp import ClientSession
from discord.ext import commands

from utils import database
from utils.configs import BotConfig
from utils.functions import get_modules
from utils.objects import Object


class TreasureMiner(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=">",
            description="A discord bot to monitor current Devilfruit Circulation from the MineMineNoMi mod",
            status=discord.Status.dnd,
            activity=discord.Game(f"Starting Up..."),
            intents=discord.Intents.all(),
            chunk_guilds_at_startup=True,
            allowed_mentions=discord.AllowedMentions(replied_user=False),
        )
        self.modules_ready = asyncio.Event()
        self.path = Path(__file__).parent
        self.modules_path = self.path.joinpath("modules")
        self.remove_command("help")
        self.load_config()

    def load_config(self):
        """Loads the bot's config."""
        config = yaml.safe_load(open("config.yaml"))
        self.config = BotConfig(**config)

    async def setup_constants(self):
        """Sets up bot's constants."""
        self._last_exception = None
        self.constants = Object()
        self.GOLDEN_COLOR = 0xFFD700
        self.constants.RSession = ClientSession()

    async def load_database(self):
        database_path = self.path.joinpath("database/data.db")
        database_path.parent.mkdir(parents=True, exist_ok=True)
        self.db = await asqlite.connect(database_path)
        print("Connected to database.")
        await database.build(self.db)

    async def load_modules(self):
        """Loads all modules."""
        for module in get_modules(self.modules_path):
            await self.load_extension(module.spec)
            print(f"Loaded module {module.name}")

    async def setup_hook(self):
        """Bot's startup function."""
        await self.setup_constants()
        await self.load_database()
        await self.load_modules()
        asyncio.create_task(self.change_status())

    async def change_status(self):
        """Changes the bot's status after a successful startup."""
        await self.wait_until_ready()
        self.modules_ready.set()
        await self.change_presence(status=discord.Status.online)

    def run(self, **kwargs):
        # Run the bot
        super().run(self.config.discord_api_key, **kwargs)

    async def on_message(self, message):
        """Handles messages and commands sent to the bot by owners."""
        if message.author.id not in self.config.bot_owners:
            return
        await self.process_commands(message)


if __name__ == "__main__":
    try:
        bot = TreasureMiner()
        bot.run(reconnect=True)
    except KeyboardInterrupt:
        print("Shutting down bot...")
