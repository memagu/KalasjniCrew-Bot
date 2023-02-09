import discord
import math
import os
import sys
import datetime

sys.path.append("../")
from credentials import KCBot

from discord.ext import commands

command_prefix = "!kc "

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix=command_prefix, intents=intents)


@bot.event
async def on_ready():
    print(f"Logged on as {bot.user}")


@bot.event
async def on_command(ctx):
    with open("log.log", "a", encoding="utf-8") as log:
        log.write(f"[{datetime.datetime.now()}] [{ctx.author}] {ctx.message.content}\n")


@bot.command(brief="Replies pong | No arguments required")
async def ping(ctx):
    await ctx.send("pong")


@bot.command(brief="Repeats a phrase a number of times | <content> <amount>")
async def repeat(ctx, *args):
    phrase, amount = " ".join(args[:-1]), int(args[-1])

    if ctx.message.mention_everyone:
        await ctx.send("Please refrain from mentioning everyone")
        return

    for _ in range(min(25, amount)):
        await ctx.send(phrase)
        await ctx.channel.purge(limit=1)


@bot.command(brief="Clear a number of messages | <amount>")
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=min(32, amount + 1))


@bot.command(brief="Make a wave | <phrase> <periods>")
async def wave(ctx, *args):
    phrase, periods = " ".join(args[:-1]), min(4, int(args[-1]))

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

    while angle < (2 * math.pi / b) * periods:
        segment = f"{filler * int((a * math.sin(b * (angle + c)) + d))}{phrase}"
        await ctx.send(segment)

        angle += angle_velocity


@bot.command(brief="Send songs stored bangers | No arguments required")
async def bangers(ctx):
    for filepath in os.scandir("./assets/audio"):
        await ctx.send(file=discord.File(filepath))


@bot.command(brief="Get member information | <@member>")
async def info(ctx):
    member = ctx.message.mentions[0]
    member_attributes = [["activities", member.activities],
                       ["activity", member.activity],
                       ["avatar", member.avatar],
                       ["avatar_url", member.avatar_url],
                       ["bot", member.bot],
                       ["color", member.color],
                       ["colour", member.colour],
                       ["created_at", member.created_at],
                       ["default_avatar", member.default_avatar],
                       ["default_avatar_url", member.default_avatar_url],
                       ["desktop_status", member.desktop_status],
                       ["discriminator", member.discriminator],
                       ["display_name", member.display_name],
                       ["dm_channel", member.dm_channel],
                       ["guild", member.guild],
                       ["guild_permissions", member.guild_permissions],
                       ["id", member.id],
                       ["joined_at", member.joined_at],
                       ["mention", member.mention],
                       ["mobile_status", member.mobile_status],
                       ["mutual_guilds", member.mutual_guilds],
                       ["name", member.name],
                       ["nick", member.nick],
                       ["pending", member.pending],
                       ["premium_since", member.premium_since],
                       ["public_flags", member.public_flags],
                       ["raw_status", member.raw_status],
                       ["roles", member.roles],
                       ["status", member.status],
                       ["system", member.system],
                       ["top_role", member.top_role],
                       ["voice", member.voice],
                       ["web_status", member.web_status]]
    await ctx.send("\n".join([f"{attribute}={value}" for attribute, value in member_attributes]))


@bot.command(brief="Evaluate python code | <expression>")
async def pyeval(ctx, *args):
    expression = " ".join(args)
    await ctx.send(f"{expression} returned:\n```{eval(expression)}```")


@bot.command(brief="Encrypt plain text | <plain_text> <key>")
async def encrypt(ctx, *args):
    plain_text, key = " ".join(args[:-1]), int(args[-1])

    cipher_text = "".join(chr(pow(ord(char), key, 143)) for char in plain_text)

    await ctx.channel.purge(limit=1)
    await ctx.send(f"Cipher text: ```{cipher_text}```")


@bot.command(brief="Decrypt cipher text | <cipher_text> <key>")
async def decrypt(ctx, *args):
    cipher_text, key = " ".join(args[:-1]), int(args[-1])

    plain_text = "".join(chr(pow(ord(char), key, 143)) for char in cipher_text)

    await ctx.channel.purge(limit=1)
    await ctx.send(f"Plain text: ```{plain_text}```")


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


bot.run(KCBot.API_TOKEN)
