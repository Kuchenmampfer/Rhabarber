import asyncpg
import discord

from views.spielewahl import Spielewahl


class Spieleliste(discord.ui.View):
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
        self.current_embed_index = 0
        self.embeds = []
        self.previous_button = discord.ui.Button(label='🔼', style=discord.ButtonStyle.green,
                                                 custom_id='spieleliste:previous_button')
        self.previous_button.callback = self.go_to_previous
        self.next_button = discord.ui.Button(label='🔽', style=discord.ButtonStyle.green,
                                             custom_id='spieleliste:next_button')
        self.next_button.callback = self.go_to_next
        self.select_button = discord.ui.Button(label='Spiele wählen', style=discord.ButtonStyle.green,
                                               custom_id='spieleliste:select_button')
        self.select_button.callback = self.send_select_message
        super().__init__(self.previous_button, self.next_button, self.select_button, timeout=None)

    async def get_embeds(self):
        async with self.pool.acquire() as conn:
            game_records = await conn.fetch('''
                                            SELECT g.name, COUNT(p.member_id)
                                            FROM game_players p
                                            RIGHT JOIN games g
                                                ON p.game_id = g.id
                                            GROUP BY g.name
                                            ORDER BY g.name
                                            ''')
            for i in range(len(game_records)):
                if i % 10 == 0:
                    self.embeds.append(discord.Embed(colour=discord.Colour.blue(), title=f'Spiele ({i // 10})'))
                self.embeds[-1].add_field(name=game_records[i][0], value=game_records[i][1])

    async def go_to_previous(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.current_embed_index -= 1
        await self.update_spieleliste(interaction)

    async def go_to_next(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.current_embed_index += 1
        await self.update_spieleliste(interaction)

    async def send_select_message(self, interaction: discord.Interaction):
        spielewahl = Spielewahl(self.pool, interaction.user.id, interaction.guild_id)
        await spielewahl.add_selects()
        await interaction.response.send_message('Wähle deine Spiele weise', view=spielewahl, ephemeral=True)

    async def update_spieleliste(self, interaction: discord.Interaction):
        await interaction.edit_original_message(embed=self.embeds[self.current_embed_index % 10], view=self)
