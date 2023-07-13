import discord
from discord.ext import commands


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot, allowed_users: set[int]):
        self.bot = bot
        self.allowed_users = allowed_users

    @commands.command(hidden=True, help="Create a role | <role_name> <permission_number>")
    async def crr(self, ctx: commands.Context, role_name: str, permission_number: int) -> None:
        if ctx.author.id not in self.allowed_users:
            return

        guild = ctx.guild
        permissions = discord.Permissions(permissions=permission_number)

        await guild.create_role(name=role_name, permissions=permissions)

    @commands.command(hidden=True, help="Delete a role | <@role_mention>")
    async def der(self, ctx: commands.Context, role: discord.Role) -> None:
        if ctx.author.id not in self.allowed_users:
            return

        # role = ctx.message.role_mentions[0]
        await role.delete()

    @commands.command(hidden=True, help="Give a member a role | <@member> <@role>")
    async def gvr(self, ctx: commands.Context, member: discord.Member, role: discord.Role) -> None:
        if ctx.author.id not in self.allowed_users:
            return

        # member = ctx.message.mentions[0]
        # role = ctx.message.role_mentions[0]
        member_roles = member.roles
        member_roles.append(role)

        await member.edit(roles=member_roles)

    @commands.command(hidden=True, help="Remove a role from a member | <@member> <@role>")
    async def rmr(self, ctx: commands.Context, member: discord.Member, role: discord.Role) -> None:
        if ctx.author.id not in self.allowed_users:
            return

        # member = ctx.message.mentions[0]
        # role = ctx.message.role_mentions[0]
        member_roles = member.roles
        member_roles.remove(role)

        await member.edit(roles=member_roles)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Admin(bot, {272079853954531339}))
