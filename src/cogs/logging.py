import logging

from discord import ApplicationContext, Bot, Cog

class Logging(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

        logging.basicConfig(
            format="%(asctime)s - %(levelname)s - %(message)s",
            level=logging.INFO
        )

    @Cog.listener()
    async def on_ready(self) -> None:
        await self.bot.sync_commands()
        logging.info(f"Logged on as {self.bot.user}")

    @Cog.listener()
    async def on_application_command(self, ctx: ApplicationContext) -> None:
        user = f"{ctx.author} (ID: {ctx.author.id})"
        command = f"/{ctx.command.qualified_name}"
        guild = f"{ctx.guild.name} (ID: {ctx.guild.id})" if ctx.guild else "DM"
        options = ", ".join(option["value"] for option in ctx.selected_options or [])

        logging.info(f"{user}@{guild}: {command} {options}")

    @Cog.listener()
    async def on_application_command_error(self, _, error) -> None:
        logging.error(error)


def setup(bot: Bot) -> None:
    bot.add_cog(Logging(bot))

