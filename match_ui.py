import asyncio
import logging

import discord
from discord import app_commands

from balancer import balance
from models import RANKS


def recruitment(match):
    embed = discord.Embed(title='VALORANT カスタム募集', color=0xFA4454)
    embed.description = f'主催：<@{match.owner_id}>\n参加者：{len(match.participants)} / 10'
    entries = [f'{index}. <@{user}> — {RANKS[rank - 1]}' for index, (user, rank) in enumerate(match.participants.items(), 1)]
    embed.add_field(name='参加者', value='\n'.join(entries) or '参加者を募集中です。', inline=False)
    embed.set_footer(text='初めての方はランクを選択してから参加してください。再起動後は新しく募集してください。')
    return embed


class MatchView(discord.ui.View):
    def __init__(self, match, service, profiles):
        super().__init__(timeout=None)
        self.match, self.service, self.profiles = match, service, profiles
        self.lock = asyncio.Lock()

    async def operate(self, interaction, action, rank=None):
        await interaction.response.defer(ephemeral=True)
        async with self.lock:
            try:
                match = self.match
                user_id = interaction.user.id
                if match.closed:
                    raise ValueError('この募集は終了しています。新しく募集してください。')
                if action in ('split', 'close') and user_id != match.owner_id:
                    raise ValueError('この操作は主催者のみ実行できます。')
                if action == 'rank':
                    self.profiles.set(user_id, rank)
                    if user_id in match.participants:
                        match.participants[user_id] = rank
                    notice = f'{RANKS[rank - 1]}を登録しました。未参加なら「参加」を押してください。'
                elif action == 'join':
                    registered = self.profiles.get(user_id)
                    if registered is None:
                        raise ValueError('先にランクを選択してください。')
                    self.service.join(match, user_id, registered)
                    notice = '参加しました。'
                elif action == 'leave':
                    self.service.leave(match, user_id)
                    notice = '辞退しました。'
                elif action == 'split':
                    first, second = balance(match.participants)
                    result = discord.Embed(title='チーム分け結果', color=0xFA4454)
                    scores = []
                    for label, team in (('α', first), ('β', second)):
                        score = sum(match.participants[user] for user in team)
                        scores.append(score)
                        result.add_field(name=f'チーム{label}：合計{score}', value='\n'.join(f'<@{user}> — {RANKS[match.participants[user] - 1]}' for user in team), inline=False)
                    result.set_footer(text=f'ランク点の差：{abs(scores[0] - scores[1])} ｜ 自己申告ランクによる目安です。次の試合は /match create')
                    # Publish successfully before closing the session.
                    await interaction.message.edit(embed=result, view=None)
                    self.service.close(match)
                    self.stop()
                    await interaction.followup.send('チーム分けを確定しました。', ephemeral=True)
                    return
                elif action == 'close':
                    await interaction.message.edit(content='この募集は主催者が終了しました。', embed=None, view=None)
                    self.service.close(match)
                    self.stop()
                    await interaction.followup.send('募集を終了しました。', ephemeral=True)
                    return
                await interaction.message.edit(embed=recruitment(match), view=self)
                await interaction.followup.send(notice, ephemeral=True)
            except ValueError as error:
                await interaction.followup.send(str(error), ephemeral=True)
            except Exception:
                logging.exception('募集操作に失敗しました')
                await interaction.followup.send('保存または表示の更新に失敗しました。参加状況を確認してください。', ephemeral=True)

    @discord.ui.select(placeholder='現在のランクを選択', options=[discord.SelectOption(label=name, value=str(index)) for index, name in enumerate(RANKS, 1)], row=0)
    async def select_rank(self, interaction: discord.Interaction, select: discord.ui.Select):
        # Read this interaction's value, not mutable shared Select state.
        await self.operate(interaction, 'rank', int(interaction.data['values'][0]))

    @discord.ui.button(label='参加', style=discord.ButtonStyle.success, row=1)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.operate(interaction, 'join')

    @discord.ui.button(label='辞退', style=discord.ButtonStyle.secondary, row=1)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.operate(interaction, 'leave')

    @discord.ui.button(label='チーム分け', style=discord.ButtonStyle.primary, row=1)
    async def split(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.operate(interaction, 'split')

    @discord.ui.button(label='募集終了', style=discord.ButtonStyle.danger, row=1)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.operate(interaction, 'close')


def register_commands(tree, service, profiles):
    group = app_commands.Group(name='match', description='カスタムの参加募集とチーム分け', guild_only=True)

    @group.command(name='create', description='10人のカスタム参加募集を開始します')
    async def create(interaction: discord.Interaction):
        try:
            match = service.create(interaction.channel_id, interaction.user.id)
        except ValueError as error:
            await interaction.response.send_message(str(error), ephemeral=True)
            return
        view = MatchView(match, service, profiles)
        try:
            await interaction.response.send_message(embed=recruitment(match), view=view)
        except Exception:
            service.close(match)
            view.stop()
            raise

    @tree.command(name='profile', description='自分の登録ランクを確認します')
    @app_commands.guild_only()
    async def profile(interaction: discord.Interaction):
        rank = profiles.get(interaction.user.id)
        text = f'登録ランク：{RANKS[rank - 1]}' if rank else 'ランク未登録です。募集メッセージの選択メニューから登録してください。'
        await interaction.response.send_message(text, ephemeral=True)

    tree.add_command(group)
