import base64
import datetime
import math
import os
import re

import discord
from discord.ext import commands
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

COMMAND_PREFIX = "!kc "

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=discord.Intents.all())


@bot.event
async def on_ready():
    print(f"Logged on as {bot.user}", flush=True)


@bot.event
async def on_command(ctx):
    print(f"[{datetime.datetime.now()}] [{ctx.author}] {ctx.message.content}", flush=True)


@bot.command(help="Replies pong | No arguments required")
async def ping(ctx):
    await ctx.send("pong")


@bot.command(help="Repeats a phrase a number of times | <repetitions> <phrase>")
async def repeat(ctx, repetitions: int, *, phrase: str):
    if ctx.message.mention_everyone:
        await ctx.send("Please refrain from mentioning everyone")
        return

    for _ in range(min(25, repetitions)):
        await ctx.send(phrase)
        await ctx.channel.purge(limit=1)


@bot.command(help="Clear a number of messages | <amount>")
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=min(32, amount + 1))


@bot.command(help="Make a wave | <periods> <phrase>")
async def wave(ctx, periods: lambda x: min(4.0, float(x)), *, phrase: str):
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


@bot.command(help="Send songs stored bangers | No arguments required")
async def bangers(ctx):
    for filepath in os.scandir("./assets/audio"):
        await ctx.send(file=discord.File(filepath))


@bot.command(help="Get member information | <@member>")
async def info(ctx):
    attributes = []

    member = ctx.message.mentions[0]
    for name in dir(member):
        if name.startswith('_'):
            continue

        attribute = getattr(member, name)

        if callable(attribute):
            continue

        attributes.append(f"{name}={attribute}")

    await ctx.send('\n'.join(attributes))


@bot.command(help="Evaluate python code (expressions may need to be wrapped in quotes) | <expression>")
async def pyeval(ctx, expression: str):
    await ctx.send(f"{expression} evaluated to:\n```{eval(expression)}```")


@bot.command(help="Encrypt plain text | <key> <plain_text>")
async def encrypt(ctx, key: int, *, plain_text: str):
    cipher_text = "".join(chr(pow(ord(char), key, 143)) for char in plain_text)

    await ctx.channel.purge(limit=1)
    await ctx.send(f"Cipher text: ```{cipher_text}```")


@bot.command(help="Decrypt cipher text | <key> <cipher_text> ")
async def decrypt(ctx, key: int, *, cipher_text: str):
    plain_text = "".join(chr(pow(ord(char), key, 143)) for char in cipher_text)

    await ctx.channel.purge(limit=1)
    await ctx.send(f"Plain text: ```{plain_text}```")


@bot.command(help="Get the latest steam 2fa code for propullur | No arguments required")
async def propullur(ctx):
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


@bot.command(hidden=True, help="Create a role | <role_name> <permission_number>")
async def crr(ctx, role_name: str, permission_number: int):
    if ctx.author.id != 272079853954531339:
        return

    guild = ctx.guild
    permissions = discord.Permissions(permissions=permission_number)
    await guild.create_role(name=role_name, permissions=permissions)


@bot.command(hidden=True, help="Delete a role | <@role_mention>")
async def der(ctx):
    if ctx.author.id != 272079853954531339:
        return

    role = ctx.message.role_mentions[0]
    await role.delete()


@bot.command(hidden=True, help="Give a member a role | <@member> <@role>")
async def gvr(ctx):
    if ctx.author.id != 272079853954531339:
        return

    member = ctx.message.mentions[0]
    role = ctx.message.role_mentions[0]
    member_roles = member.roles
    member_roles.append(role)
    await member.edit(roles=member_roles)


@bot.command(hidden=True, help="Remove a role from a member | <@member> <@role>")
async def rmr(ctx):
    if ctx.author.id != 272079853954531339:
        return

    member = ctx.message.mentions[0]
    role = ctx.message.role_mentions[0]
    member_roles = member.roles
    member_roles.remove(role)
    await member.edit(roles=member_roles)


def main():
    load_dotenv()
    bot.run(os.getenv("DISCORD_API_TOKEN"))


if __name__ == "__main__":
    main()
