import discord
from discord.ext import commands

from views.spieleliste import Spieleliste


class SendMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name='send_message', guild_ids=[805155951324692571])
    async def send_message(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        spieleliste = Spieleliste(self.bot.pool)
        await spieleliste.get_embeds()
        try:
            message = await ctx.respond(view=spieleliste, embed=spieleliste.embeds[spieleliste.current_embed_index])
        except IndexError:
            await ctx.respond('Ihr habt noch keine Spiele gespeichert, hier gibt es nichts zu sehen.')
            spieleliste.stop()
            return
        with open('message_id.txt', 'w', encoding='utf-8') as f:
            f.write(str(message.id))


def setup(bot):
    bot.add_cog(SendMessage(bot))
