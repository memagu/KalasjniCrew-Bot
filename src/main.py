import os
from pathlib import Path

import discord
from dotenv import load_dotenv

COG_DIRECTORY = Path("./cogs")


def load_cogs(bot: discord.Bot) -> None:
    for filename in COG_DIRECTORY.rglob("*.py"):
        extension_path: str = filename.with_suffix("").as_posix().replace("/", ".")
        bot.load_extension(extension_path)


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

