import math
import os

import discord
from discord.ext import commands


class Tools(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(help="Repeats a phrase a number of times | <repetitions> <phrase>")
    async def repeat(self, ctx: commands.Context, repetitions: int, *, phrase: str) -> None:
        if ctx.message.mention_everyone:
            await ctx.send("Please refrain from mentioning everyone")
            return

        for _ in range(min(25, repetitions)):
            await ctx.send(phrase)
            await ctx.channel.purge(limit=1)

    @commands.command(help="Purge a number of messages | <amount>")
    async def purge(self, ctx: commands.Context, amount: int) -> None:
        await ctx.channel.purge(limit=min(32, amount + 1))

    @commands.command(help="Make a wave | <periods> <phrase>")
    async def wave(self, ctx: commands.Context, periods: lambda x: min(8.0, float(x)), *, phrase: str) -> None:
        if ctx.message.mention_everyone:
            await ctx.send("Please refrain from mentioning everyone")
            return

        filler = "."
        a = 60
        b = 0.25
        c = 0
        d = 60

        angle = 0
        angle_velocity = math.pi / 10

        wave_part = ""

        while angle < (2 * math.pi / b) * periods:
            segment = f"{filler * int((a * math.sin(b * (angle + c)) + d))}{phrase}\n"

            if len(wave_part) + len(segment) > 2000:
                await ctx.send(wave_part)
                wave_part = ""

            wave_part += segment
            angle += angle_velocity

        await ctx.send(wave_part)

    @commands.command(help="Send songs stored bangers | No arguments required")
    async def bangers(self, ctx: commands.Context) -> None:
        for filepath in os.scandir("../assets/music_bank"):
            await ctx.send(file=discord.File(filepath))

    @commands.command(help="Evaluate a python expression (expression may need to be wrapped in quotes) | <expression>")
    async def pyeval(self, ctx: commands.Context, expression: str) -> None:
        await ctx.send(f"{expression} evaluated to:\n```{eval(expression)}```")


class RSA(commands.Cog):
    def __init__(self, bot: commands.Bot, mod: int):
        self.bot = bot
        self.mod = mod

    @commands.command(help="Encrypt plain text | <key> <plain_text>")
    async def encrypt(self, ctx: commands.Context, key: int, *, plain_text: str):
        cipher_text = "".join(chr(pow(ord(char), key, self.mod)) for char in plain_text)

        await ctx.channel.purge(limit=1)
        await ctx.send(f"Cipher text: ```{cipher_text}```")

    @commands.command(help="Decrypt cipher text | <key> <cipher_text> ")
    async def decrypt(self, ctx: commands.Context, key: int, *, cipher_text: str):
        plain_text = "".join(chr(pow(ord(char), key, self.mod)) for char in cipher_text)

        await ctx.channel.purge(limit=1)
        await ctx.send(f"Plain text: ```{plain_text}```")


def setup(bot: commands.Bot):
    bot.add_cog(Tools(bot))
    bot.add_cog(RSA(bot, 143))
