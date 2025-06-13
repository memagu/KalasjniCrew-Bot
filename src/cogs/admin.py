from discord import ApplicationContext, Bot, Cog, Member, Option, Permissions, Role, slash_command
import requests


class Admin(Cog):
    def __init__(self, bot: Bot, allowed_users: set[int]):
        self.bot = bot
        self.allowed_users = allowed_users

    def is_allowed(self, ctx: ApplicationContext) -> bool:
        return ctx.author.id in self.allowed_users

    @slash_command(description="Create a role with custom permissions")
    async def create_role(
        self,
        ctx: ApplicationContext,
        role_name: Option(str, description="Name of the role"),
        permission_number: Option(int, description="Permission number"),
    ) -> None:
        if not self.is_allowed(ctx):
            await ctx.respond("You are not authorized to use this command.", ephemeral=True)
            return

        permissions = Permissions(permissions=permission_number)
        await ctx.guild.create_role(name=role_name, permissions=permissions)
        await ctx.respond(f"Role `{role_name}` created successfully!")

    @slash_command(description="Delete a role from the server")
    async def delete_role(
        self,
        ctx: ApplicationContext,
        role: Option(Role, description="Role to delete"),
    ) -> None:
        if not self.is_allowed(ctx):
            await ctx.respond("You are not authorized to use this command.", ephemeral=True)
            return

        await role.delete()
        await ctx.respond(f"Role `{role.name}` has been deleted.")

    @slash_command(description="Give a member a role")
    async def give_role(
        self,
        ctx: ApplicationContext,
        member: Option(Member, description="Member to give the role"),
        role: Option(Role, description="Role to give"),
    ) -> None:
        if not self.is_allowed(ctx):
            await ctx.respond("You are not authorized to use this command.", ephemeral=True)
            return

        await member.add_roles(role)
        await ctx.respond(f"Role `{role.name}` added to {member.mention}.")

    @slash_command(description="Remove a role from a member")
    async def remove_role(
        self,
        ctx: ApplicationContext,
        member: Option(Member, description="Member to remove the role from"),
        role: Option(Role, description="Role to remove"),
    ) -> None:
        if not self.is_allowed(ctx):
            await ctx.respond("You are not authorized to use this command.", ephemeral=True)
            return

        await member.remove_roles(role)
        await ctx.respond(f"Role `{role.name}` removed from {member.mention}.")

    @slash_command(description="Get the bot's external IP address")
    async def ip(
        self,
        ctx: ApplicationContext,
    ) -> None:
        if not self.is_allowed(ctx):
            await ctx.respond("You are not authorized to use this command.", ephemeral=True)
            return

        response = requests.get("https://icanhazip.com")

        if not response.ok:
            await ctx.respond("Failed to get IP address.")
            return

        ip_address = response.text.strip()
        await ctx.respond(f"External IP Address: `{ip_address}`")


def setup(bot: Bot) -> None:
    bot.add_cog(Admin(bot, {272079853954531339}))

