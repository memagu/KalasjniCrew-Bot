import discord
import os
import math
import time
from keep_alive import keep_alive
from Other_Projects.my_secrets import KCbot

intents = discord.Intents.default()
intents.members = True

TOKEN = KCbot.API_TOKEN
client = discord.Client(intents=intents)

@client.event
async def on_ready():
  print('Logged on as {0.user}!'.format(client))

  global guild
  guild = client.get_guild(id=371615862148300801)
  print(guild)

  global carl
  carl = guild.get_member(235453788939354112)
  print(carl.nick)

  global simon
  simon = guild.get_member(286578157010550784)
  print(simon.nick)

  global david
  david = guild.get_member(346723302989103108)
  print(david.nick)

  global carl_nick
  carl_nick = False

  global simon_nick
  simon_nick = False

  global david_nick
  david_nick = False


@client.event
async def on_message(message):
  if message.author == client.user:
    return

  msg = message.content

  #print(message)
  #print(message.author.id)
  #print(client)

  if msg.startswith("!kc help"):
    await message.channel.send_message("""
    !kc ping <single word> <amount>
    !kc clear <amount>
    !kc wave <phrase> <amount> <filler>
    !kc bangers
    """)

  if msg.startswith("!kc hello"):
    await message.channel.send_message("hello")

  if msg.startswith("!kc ping"):
    amount = int(msg.split(maxsplit=3)[-1])
    print(amount)
    if amount > 20:
      amount = 20
    if msg.split(maxsplit=3)[-2] != "@everyone":
      for i in range(amount):
        await message.channel.send_message(msg.split(maxsplit=3)[-2])
        await message.channel.purge(limit=1)
    else:
      await message.channel.purge(limit=1)
      await message.channel.send_message("Please don't ping everyone.")

  if msg.startswith("!kc clear"):
    amount = int(msg.split(maxsplit=2)[-1])
    if 0 > amount or amount > 100:
      await message.channel.send_message("You must clear at least no messages and at most 100.")
    else:
      await message.channel.purge(limit=(amount + 1))

  if msg.startswith("!kc wave"):
    amplitude = 20
    frequenzy = 5
    amount = int(amplitude * frequenzy / 2)
    phrase = "."
    filler = chr(32)

    phrase = "".join(str(x) for x in msg.split()[2:-2])
    amount = int(msg.split()[-2])
    filler = (msg.split()[-1])

    for x in range(amount):
        y = math.sin(x/frequenzy) + 1
        await message.channel.send_message(filler * math.ceil(y * amplitude) + phrase)

  if msg.startswith("!kc bangers"):
    await message.channel.send_message()
    await message.channel.send_message()
    await message.channel.send_message()

  if msg.startswith("!kc c4r1"):
    global carl_nick
    if carl_nick:
      carl_nick = False
    else:
      carl_nick = True
      while carl_nick:
        await carl.edit(nick=":|")
        time.sleep(1)
        await carl.edit(nick=":/")
        time.sleep(1)
        await carl.edit(nick=":—")
        time.sleep(1)
        await carl.edit(nick=":\\")
        time.sleep(1)

  if msg.startswith("!kc s1m0n"):
    global simon_nick
    if simon_nick:
      simon_nick = False
      time.sleep(8)
      await simon.edit(nick="💿pRoddarn💿")
    else:
      simon_nick = True
      while simon_nick:
        await simon.edit(nick="💿Proddarn💿")
        time.sleep(1)
        await simon.edit(nick="💿pRoddarn💿")
        time.sleep(1)
        await simon.edit(nick="💿prOddarn💿")
        time.sleep(1)
        await simon.edit(nick="💿proDdarn💿")
        time.sleep(1)
        await simon.edit(nick="💿prodDarn💿")
        time.sleep(1)
        await simon.edit(nick="💿proddArn💿")
        time.sleep(1)
        await simon.edit(nick="💿proddaRn💿")
        time.sleep(1)
        await simon.edit(nick="💿proddarN💿")
        time.sleep(1)

  if msg.startswith("!kc d4v1d"):
    global david_nick
    if david_nick:
      david_nick = False
      time.sleep(5)
      await david.edit(nick="<½12§]")
    else:
      david_nick = True
      while david_nick:
        await david.edit(nick="<½12§]")
        time.sleep(1)
        await david.edit(nick="]<½12§")
        time.sleep(1)
        await david.edit(nick="§]<½12")
        time.sleep(1)
        await david.edit(nick="2§]<½1")
        time.sleep(1)
        await david.edit(nick="12§]<½")
        time.sleep(1)
        await david.edit(nick="½12§]<")
        time.sleep(1)



keep_alive()
client.run(os.environ['TOKEN'])

