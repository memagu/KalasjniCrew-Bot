from discord import ApplicationContext, Bot, Cog, Option, slash_command


class RSA(Cog):
    def __init__(self, bot: Bot, mod: int):
        self.bot = bot
        self.mod = mod

    @slash_command(description="Encrypt plain text | <key> <plain_text>")
    async def encrypt(
            self,
            ctx: ApplicationContext,
            key: Option(int, description="Encryption key"),
            plain_text: Option(str, description="Plain text to encrypt")
    ) -> None:
        cipher_text = "".join(chr(pow(ord(char), key, self.mod)) for char in plain_text)
        await ctx.respond(f"Cipher text:\n```{cipher_text}```")

    @slash_command(description="Decrypt cipher text | <key> <cipher_text>")
    async def decrypt(
            self,
            ctx: ApplicationContext,
            key: Option(int, description="Decryption key"),
            cipher_text: Option(str, description="Cipher text to decrypt")
    ) -> None:
        plain_text = "".join(chr(pow(ord(char), key, self.mod)) for char in cipher_text)
        await ctx.respond(f"Plain text:\n```{plain_text}```")


def setup(bot: Bot) -> None:
    bot.add_cog(RSA(bot, 143))
