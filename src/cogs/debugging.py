from datetime import datetime

import discord
from discord.ext import commands
from discord.utils import escape_mentions


class Debugging(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(help="Replies with \"pong\" | No arguments required")
    async def ping(self, ctx: commands.Context) -> None:
        await ctx.send("pong")

    @commands.command(help="Get member information | <@member>")
    async def info(self, ctx, member: discord.Member) -> None:
        attributes = []

        for name in dir(member):
            if name.startswith('_'):
                continue

            attribute = getattr(member, name)

            if callable(attribute):
                continue

            attributes.append(f"{name}={attribute}")

        attribute_str = escape_mentions('\n'.join(attributes))

        if len(attribute_str) <= 2000:
            await ctx.send(attribute_str)
            return

        for chunk in (attribute_str[i:i + 2000] for i in range(0, len(attribute_str), 2000)):
            await ctx.send(chunk)


class Logging(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        print(f"Logged on as {self.bot.user}", flush=True)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: discord.DiscordException):
        print(f"[{datetime.now()}] [ERROR] {error}", flush=True)

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context) -> None:
        print(f"[{datetime.now()}] [{ctx.author}] {ctx.message.content}", flush=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Debugging(bot))
    await bot.add_cog(Logging(bot))
