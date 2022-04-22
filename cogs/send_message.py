import discord
from discord.ext import commands

from views.spieleliste import Spieleliste


class SendMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name='send_message', guild_ids=[805155951324692571])
    async def send_message(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        spieleliste = Spieleliste(self.bot)
        await spieleliste.get_embeds(ctx.guild_id)
        try:
            message = await ctx.send(view=spieleliste, embed=spieleliste.embeds[spieleliste.current_embed_index])
        except IndexError:
            await ctx.respond('Ihr habt noch keine Spiele gespeichert, hier gibt es nichts zu sehen.')
            spieleliste.stop()
            return
        await ctx.respond('||Rhabarberbarbarabarbarbarenbartbarbier||', ephemeral=True)
        with open('message_ids.txt', 'r+', encoding='utf-8') as f:
            for line in f.readlines():
                if f':{ctx.guild_id}' in line:
                    [message_id, channel_id, guild_id] = [int(some_id) for some_id in line.split(':')]
                    old_channel = await self.bot.fetch_channel(channel_id)
                    old_message = await old_channel.fetch_message(message_id)
                    await old_message.delete()
                else:
                    f.write(line)
            f.write(f'{message.id}:{ctx.channel_id}:{ctx.guild_id}\n')


def setup(bot):
    bot.add_cog(SendMessage(bot))
