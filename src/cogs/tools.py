import math
import os

from discord import ApplicationContext, Bot, Cog, Option, slash_command


class Tools(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @slash_command(description="Repeats a phrase a number of times | <repetitions> <phrase>")
    async def repeat(
        self,
        ctx: ApplicationContext,
        repetitions: Option(int, description="Number of repetitions"),
        phrase: Option(str, description="Phrase to repeat")
    ) -> None:
        if "@everyone" in phrase or "@here" in phrase:
            await ctx.respond("Please refrain from mentioning everyone", ephemeral=True)
            return

        repetitions = min(25, repetitions)
        for _ in range(repetitions):
            await ctx.send(phrase)

    @slash_command(description="Purge a number of messages | <amount>")
    async def purge(
        self,
        ctx: ApplicationContext,
        amount: Option(int, description="Number of messages to purge")
    ) -> None:
        await ctx.channel.purge(limit=min(32, amount + 1))
        await ctx.respond(f"Purged {min(32, amount)} messages.", ephemeral=True)

    @slash_command(description="Make a wave | <periods> <phrase>")
    async def wave(
        self,
        ctx: ApplicationContext,
        periods: Option(float, description="Number of wave periods", min_value=0.1, max_value=8.0),
        phrase: Option(str, description="Phrase to use in the wave")
    ) -> None:
        if "@everyone" in phrase or "@here" in phrase:
            await ctx.respond("Please refrain from mentioning everyone", ephemeral=True)
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

        if wave_part:
            await ctx.send(wave_part)

        await ctx.respond("Wave sent.", ephemeral=True)

    @slash_command(description="Send songs stored in bangers | No arguments required")
    async def bangers(
        self,
        ctx: ApplicationContext
    ) -> None:
        await ctx.defer()
        for filepath in os.scandir("../assets/music_bank"):
            await ctx.send(file=discord.File(filepath))

    @slash_command(description="Evaluate a python expression (dangerous) | <expression>")
    async def pyeval(
        self,
        ctx: ApplicationContext,
        expression: Option(str, description="Python expression to evaluate")
    ) -> None:
        try:
            result = eval(expression)
            await ctx.respond(f"{expression} evaluated to:\n```{result}```")
        except Exception as e:
            await ctx.respond(f"Error evaluating expression:\n```{e}```")


def setup(bot: Bot):
    bot.add_cog(Tools(bot))

