import discord
from discord.ext import commands


class CreateTables(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.is_owner()
    @commands.slash_command(name='create_tables', guild_ids=[805155951324692571])
    async def create_tables(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        async with self.bot.pool.acquire() as conn:
            await conn.execute('''
                               CREATE TABLE IF NOT EXISTS games(
                               id SERIAL PRIMARY KEY,
                               name VARCHAR(64) NOT NULL,
                               guild_id BIGINT NOT NULL,
                               role_id BIGINT,
                               channel_id BIGINT,
                               UNIQUE(name, guild_id)
                               );
                               
                               CREATE TABLE IF NOT EXISTS game_players(
                               game_id SMALLINT REFERENCES games(id) ON DELETE CASCADE,
                               member_id BIGINT NOT NULL,
                               PRIMARY KEY(game_id, member_id)
                               )
                               ''')
        await ctx.respond('Tables created :white_check_mark:')


def setup(bot):
    bot.add_cog(CreateTables(bot))
