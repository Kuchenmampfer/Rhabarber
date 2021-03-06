import asyncpg
import discord


class Select(discord.ui.Select):
    def __init__(self, index: int):
        super().__init__(min_values=0, placeholder=f'Spiele {index // 25 + 1}')
        self.game_dict: dict = {}

    def set_max_values(self):
        self.max_values = len(self.game_dict)

    async def callback(self, interaction: discord.Interaction):
        for key in self.game_dict.keys():
            self.game_dict[key] = str(key) in self.values


class Spielewahl(discord.ui.View):
    def __init__(self, spieleliste, user_id: int, guild_id):
        self.pool = spieleliste.pool
        self.user_id = user_id
        self.guild_id = guild_id
        self.select_groups = []
        self.current_group_index = 0
        self.previous_button = discord.ui.Button(label='🔼', style=discord.ButtonStyle.green,
                                                 custom_id='spieleliste:previous_button')
        self.previous_button.callback = self.go_to_previous
        self.next_button = discord.ui.Button(label='🔽', style=discord.ButtonStyle.green,
                                             custom_id='spieleliste:next_button')
        self.next_button.callback = self.go_to_next
        self.confirm_button = discord.ui.Button(label='✅', style=discord.ButtonStyle.green,
                                                custom_id='spielewahl:confirm_button')
        self.confirm_button.callback = self.confirm
        super().__init__()

    async def add_selects(self):
        async with self.pool.acquire() as conn:
            games_records: asyncpg.Record = await conn.fetch('''
                                                             SELECT name, EXISTS(
                                                                 SELECT * FROM game_players p
                                                                 WHERE p.game_id = g.id AND p.member_id = $2
                                                                 ), id
                                                             FROM games g
                                                             WHERE g.guild_id = $1
                                                             ''',
                                                             self.guild_id, self.user_id
                                                             )
        selects = []
        select = Select(0)
        for i in range(len(games_records)):
            record = games_records[i]
            if i == len(games_records) - 1:
                selects.append(select)
                self.select_groups.append(selects)
            else:
                if i % 100 == 99:
                    self.select_groups.append(selects)
                    selects = []
                if i % 25 == 24:
                    select = Select(i)
            select.game_dict[record[2]] = record[1]
            select.set_max_values()
            select.append_option(discord.SelectOption(label=record[0], value=record[2], default=record[1]))
        for menu in self.select_groups[self.current_group_index]:
            self.add_item(menu)
        if len(self.select_groups) > 1:
            self.add_item(self.next_button)
            self.add_item(self.previous_button)
        self.add_item(self.confirm_button)

    async def go_to_previous(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.current_group_index -= 1
        for menu in self.select_groups[self.current_group_index]:
            self.add_item(menu)
        self.add_item(self.confirm_button)
        await interaction.edit_original_message(view=self)

    async def go_to_next(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.current_group_index += 1
        for menu in self.select_groups[self.current_group_index]:
            self.add_item(menu)
        self.add_item(self.confirm_button)
        await interaction.edit_original_message(view=self)

    async def confirm(self, interaction: discord.Interaction):
        games = []
        for group in self.select_groups:
            for select in group:
                for game_id, val in select.game_dict.items():
                    if val:
                        games.append((game_id, self.user_id))
        async with self.pool.acquire() as conn:
            await conn.execute('''
                               DELETE FROM game_players
                               WHERE member_id = $1 AND game_id IN (
                                   SELECT id FROM games WHERE guild_id = $2
                                   )
                               ''',
                               self.user_id, self.guild_id
                               )
            await conn.executemany('''
                                   INSERT INTO game_players(game_id, member_id)
                                   VALUES($1, $2)
                                   ''',
                                   games
                                   )
            role_ids = await conn.fetch('''
                                        SELECT role_id FROM games
                                        WHERE EXISTS(
                                                SELECT * FROM game_players
                                                WHERE game_id = id and member_id = $1
                                                )
                                            AND role_id IS NOT NULL
                                        ''',
                                        self.user_id)
        await interaction.user.add_roles(*[discord.Object(record[0]) for record in role_ids])
        self.stop()
