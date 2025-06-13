from datetime import datetime

from discord import Bot, Cog

class Logging(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @Cog.listener()
    async def on_ready(self) -> None:
        await self.bot.sync_commands()
        print(f"Logged on as {self.bot.user}", flush=True)

    @Cog.listener()
    async def on_application_command_error(self, ctx, error) -> None:
        print(f"[{datetime.now()}] [ERROR] {error}", flush=True)


def setup(bot: Bot) -> None:
    bot.add_cog(Logging(bot))

