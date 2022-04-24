import asyncio
import traceback
from abc import ABC
from time import sleep

import asyncpg
import discord
from discord.ext import commands

from log_stuff.logger_setup import setup_logger
from settings import Settings
from views.spieleliste import Spieleliste


class Bot(commands.Bot, ABC):
    def __init__(self, settings: Settings):
        super().__init__(command_prefix=',',
                         case_insensitive=True,
                         intents=settings.intents,
                         help_command=None,
                         activity=discord.Game('allgemeine Spiele'))
        self.logger = setup_logger('logger', 'log_stuff/my.log', settings.webhook_url, settings.log_level)
        self.discord_logger = setup_logger('discord', 'log_stuff/discord.log', settings.webhook_url, settings.log_level)
        self.postgres_dsn_str = settings.dsn
        self.persistent_views_added = False
        self.pool = None
        asyncio.get_event_loop().run_until_complete(self.get_pool())
        sleep(4)

        for extension in settings.cogs:
            try:
                self.load_extension(extension)
            except BaseException as error:
                exc = ''.join(traceback.format_exception(type(error), error, error.__traceback__, chain=True))
                self.logger.error(exc)

    async def get_pool(self):
        self.pool = await asyncpg.create_pool(self.postgres_dsn_str)

    async def update_guild_list_message(self, guild_id: int):
        message = None
        spieleliste = Spieleliste(self)
        await spieleliste.get_embeds(guild_id)
        with open('message_ids.txt', 'r+', encoding='utf-8') as f:
            for line in f.readlines():
                if f':{guild_id}' in line:
                    [message_id, channel_id, guild_id] = [int(some_id) for some_id in line.split(':')]
                    channel = await self.fetch_channel(channel_id)
                    message = await channel.fetch_message(message_id)
                    await message.edit(embed=spieleliste.embeds[spieleliste.current_embed_index])

    async def on_ready(self):
        self.logger.warning(f"Bot is logged in as {self.user} ID: {self.user.id}")
        with open('message_ids.txt', 'r', encoding='utf-8') as f:
            for line in f.readlines():
                [message_id, _, _] = [int(some_id) for some_id in line.split(':')]
                self.add_view(Spieleliste(self), message_id=message_id)

    async def on_resume(self):
        self.logger.warning('Resuming connection...')

    async def on_application_command_error(
            self, ctx: discord.ApplicationContext, error: discord.DiscordException
    ) -> None:
        await ctx.respond('Ooops, something went wrong. I informed my developer so he can fix it.')
        exc = ctx.command.qualified_name
        exc += ' caused the following error:\n'
        exc += ''.join(traceback.format_exception(type(error), error, error.__traceback__, chain=True))
        self.logger.error(exc)
