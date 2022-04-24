import discord

from views.spielewahl import Spielewahl


class Spieleliste(discord.ui.View):
    def __init__(self, bot):
        self.bot = bot
        self.pool = bot.pool
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
        super().__init__(timeout=None)

    async def get_embeds(self, guild_id: int):
        self.embeds = []
        async with self.pool.acquire() as conn:
            game_records = await conn.fetch('''
                                            SELECT g.name, COUNT(p.member_id)
                                            FROM game_players p
                                            RIGHT JOIN games g
                                                ON p.game_id = g.id
                                            WHERE g.guild_id = $1
                                            GROUP BY g.name
                                            ORDER BY g.name
                                            ''',
                                            guild_id)
            for i in range(len(game_records)):
                if i % 10 == 0:
                    self.embeds.append(discord.Embed(colour=discord.Colour.blue(), title=f'Spiele {i // 10 + 1}'))
                self.embeds[-1].add_field(name=game_records[i][0], value=game_records[i][1], inline=False)
        if len(self.embeds) > 1:
            self.add_item(self.next_button)
            self.add_item(self.previous_button)
        self.add_item(self.select_button)

    async def go_to_previous(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.current_embed_index -= 1
        await self.bot.update_guild_list_message(interaction.guild_id)

    async def go_to_next(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.current_embed_index += 1
        await self.bot.update_guild_list_message(interaction.guild_id)

    async def send_select_message(self, interaction: discord.Interaction):
        spielewahl = Spielewahl(self, interaction.user.id, interaction.guild_id)
        await spielewahl.add_selects()
        await interaction.response.send_message('Wähle deine Spiele weise', view=spielewahl, ephemeral=True)
        await spielewahl.wait()
        await interaction.edit_original_message(content='Spiele aktualisiert :white_check_mark:', view=None)
        await self.bot.update_guild_list_message(interaction.guild_id)
