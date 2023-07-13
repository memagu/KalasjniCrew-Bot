import asyncio
import os
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

COMMAND_PREFIX = "!kc "
COG_DIRECTORY = Path("./cogs")


async def load_cogs(bot: commands.Bot) -> None:
    for filename in os.scandir(COG_DIRECTORY):
        if filename.name.endswith(".py"):
            await bot.load_extension(f"cogs.{filename.name.removesuffix('.py')}")


async def main():
    bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=discord.Intents.all())

    await load_cogs(bot)

    load_dotenv()
    await bot.start(os.getenv("DISCORD_API_TOKEN"))


if __name__ == "__main__":
    asyncio.run(main())

