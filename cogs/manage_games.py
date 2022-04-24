import discord
from discord.ext import commands
from discord import Option
from production_secrets import guild_ids


class ManageGames(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name='add_game', guild_ids=guild_ids)
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
            if role is not None:
                await conn.executemany('''
                                       INSERT INTO game_players(game_id, member_id)
                                       VALUES((SELECT id FROM games WHERE name = $1 AND guild_id = $3), $2)
                                       ON CONFLICT DO NOTHING
                                       ''',
                                       [(name, member.id, ctx.guild_id) for member in role.members]
                                       )
        await self.bot.update_guild_list_message(ctx.guild_id)
        await ctx.respond(f'Spiel {name} hinzugefügt :white_check_mark:', ephemeral=True)

    @commands.slash_command(name='remove_game', guild_ids=[805155951324692571])
    async def remove_game(self, ctx: discord.ApplicationContext,
                          name: Option(str, description='Welches Spiel willst du löschen?'),
                          ):
        await ctx.defer()
        async with self.bot.pool.acquire() as conn:
            await conn.execute('''
                               DELETE FROM games
                               WHERE name = $1 AND guild_id = $2
                               ''',
                               name, ctx.guild_id,
                               )
        await self.bot.update_guild_list_message(ctx.guild_id)
        await ctx.respond(f'Spiel {name} gelöscht :white_check_mark:', ephemeral=True)


def setup(bot):
    bot.add_cog(ManageGames(bot))
