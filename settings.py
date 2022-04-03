import logging

from discord import Intents

import dev_secrets
import production_secrets


class Settings:
    def __init__(self, dev_mode: bool, daemon: bool):
        if dev_mode:
            self.discord_bot_token = dev_secrets.discord_bot_token
            self.dsn = dev_secrets.postgres_dsn_str
            self.webhook_url = dev_secrets.logging_webhook_url
            self.log_level = logging.DEBUG
        else:
            self.discord_bot_token = production_secrets.discord_bot_token
            self.dsn = production_secrets.postgres_dsn_str
            self.webhook_url = production_secrets.logging_webhook_url
            self.log_level = logging.INFO
        self.intents = Intents.default()
        self.cogs = initial_extensions


initial_extensions = (
    "cogs.create_tables",
    "cogs.send_message",
    "cogs.manage_games",
)
