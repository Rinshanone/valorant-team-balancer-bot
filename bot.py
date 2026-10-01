import logging
import os
from pathlib import Path

import discord
from discord import app_commands

from match_service import MatchService
from match_ui import register_commands
from profile_store import ProfileStore


class MatchBot(discord.Client):
    def __init__(self):
        # Slash commands and components do not need message-content/member intents.
        super().__init__(intents=discord.Intents.none(), allowed_mentions=discord.AllowedMentions.none())
        self.tree = app_commands.CommandTree(self)
        self.service = MatchService()
        self.profiles = ProfileStore(Path(__file__).parent / 'data' / 'profiles.json')
        register_commands(self.tree, self.service, self.profiles)

    async def setup_hook(self):
        guild_id = os.getenv('DISCORD_GUILD_ID')
        if guild_id:
            guild = discord.Object(id=int(guild_id))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()

    async def on_ready(self):
        logging.info('起動しました: %s ｜ 終了は Ctrl+C', self.user)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        raise SystemExit('環境変数 DISCORD_TOKEN にBotトークンを設定してください。')
    MatchBot().run(token)
