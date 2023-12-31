import base64
import math
import os
import re

import discord
from discord.ext import commands
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


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
        for filepath in os.scandir("../assets/audio"):
            await ctx.send(file=discord.File(filepath))

    @commands.command(help="Evaluate a python expression (expression may need to be wrapped in quotes) | <expression>")
    async def pyeval(self, ctx: commands.Context, expression: str) -> None:
        await ctx.send(f"{expression} evaluated to:\n```{eval(expression)}```")

    @commands.command(help="Get the latest steam 2FA code for propullur | No arguments required")
    async def propullur(self, ctx: commands.Context) -> None:
        credentials = Credentials.from_authorized_user_info(
            {
                "refresh_token": os.getenv("GMAIL_REFRESH_TOKEN"),
                "client_id": os.getenv("GMAIL_CLIENT_ID"),
                "client_secret": os.getenv("GMAIL_CLIENT_SECRET"),
            },
            ("https://www.googleapis.com/auth/gmail.readonly",)
        )
        service = build("gmail", "v1", credentials=credentials)

        results = service.users().messages().list(userId="me", maxResults=1,
                                                  q="from:noreply@steampowered.com").execute()
        message = service.users().messages().get(userId="me", id=results["messages"][0]["id"]).execute()
        message_content = base64.urlsafe_b64decode(message["payload"]["parts"][0]["body"]["data"]).decode("utf-8")
        steam_2fa_code = re.search(r"\n[A-Z0-9]{5}\s", message_content).group().strip()

        await ctx.send(f"This is the latest 2FA code for steam account propullur: {steam_2fa_code}")


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


async def setup(bot: commands.Bot):
    await bot.add_cog(Tools(bot))
    await bot.add_cog(RSA(bot, 143))
