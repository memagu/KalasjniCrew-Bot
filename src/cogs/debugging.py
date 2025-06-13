from discord import ApplicationContext, Bot, Cog, Member, Option, slash_command
from discord.utils import escape_mentions


class Debugging(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @slash_command(description="Replies with Pong! and shows the latency.")
    async def ping(self, ctx: ApplicationContext) -> None:
        await ctx.respond(f"Pong! Latency: {self.bot.latency * 1000:.2f} ms")

    @slash_command(description="Get detailed information about a member.")
    async def info(
        self,
        ctx: ApplicationContext,
        member: Option(Member, description="Member to get info about"),
    ) -> None:
        attributes = []

        for name in dir(member):
            if name.startswith('_'):
                continue

            attribute = getattr(member, name)

            if callable(attribute):
                continue

            attributes.append(f"{name}={attribute}")

        attribute_str = escape_mentions('\n'.join(attributes))

        for chunk in (attribute_str[i:i + 2000] for i in range(0, len(attribute_str), 2000)):
            await ctx.respond(chunk)  # Slash commands require respond(), not send()

    @slash_command(description="Kills the bot process.")
    async def kill(self, ctx: ApplicationContext) -> None:
        await ctx.respond("Shutting down...")
        await self.bot.close()


def setup(bot: Bot) -> None:
    bot.add_cog(Debugging(bot))

