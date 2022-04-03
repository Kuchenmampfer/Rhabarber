import discord
from discord.ext import commands
from discord import Option


class ManageGames(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name='add_game', guild_ids=[805155951324692571])
    async def add_game(self, ctx: discord.ApplicationContext,
                       name: Option(str, description='Wie heißt das neue Spiel?'),
                       role: Option(discord.Role) = None,
                       channel: Option(discord.TextChannel) = None
                       ):
        await ctx.defer()
        async with self.bot.pool.acquire() as conn:
            await conn.execute('''
                               INSERT INTO games(name, guild_id, role_id, channel_id)
                               VALUES($1, $2, $3, $4)
                               ON CONFLICT DO NOTHING
                               ''',
                               name, ctx.guild_id,
                               role.id if role is not None else None,
                               channel.id if channel is not None else None
                               )
            # TODO: automatically link members according to role
            # TODO: update message
        await ctx.respond(f'Spiel {name} hinzugefügt :white_check_mark:', ephemeral=True)


def setup(bot):
    bot.add_cog(ManageGames(bot))
