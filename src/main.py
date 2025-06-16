import logging
import os
from pathlib import Path

import discord
from dotenv import load_dotenv

COG_DIRECTORY = Path("./src/cogs")


def load_cogs(bot: discord.Bot) -> None:
    for filename in COG_DIRECTORY.rglob("*.py"):
        bot.load_extension(
            filename.relative_to(COG_DIRECTORY.parent).with_suffix("").as_posix().replace("/", ".")
        )


def main() -> None:
    load_dotenv()
    token: str | None = os.getenv("DISCORD_API_TOKEN")
    if token is None:
        raise RuntimeError("DISCORD_API_TOKEN is not set in .env file")

    bot = discord.Bot(intents=discord.Intents.all())

    load_cogs(bot)
    bot.run(token)


if __name__ == "__main__":
    main()

