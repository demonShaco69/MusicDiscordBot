import asyncio
import time
import requests
import discord
from discord.ext import commands
import random
import logging
import subprocess
import os
import wavelink
from data.dataOpleuhi import slappers, ways_of_delivery
from data.secretData import discordToken, wavelinkPassword, tenorToken

projectPath = os.path.dirname(os.path.abspath(__file__))
subprocess.Popen("scripts\startServer.bat", cwd=projectPath)
time.sleep(7)

TOKEN = discordToken
apikey = tenorToken

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

intents = discord.Intents.all()
intents.messages = True
intents.members = True
intents.message_content = True
dashes = ['\u2680', '\u2681', '\u2682', '\u2683', '\u2684', '\u2685']

bot = commands.Bot(command_prefix='', intents=intents)


@bot.event
async def on_ready():
    bot.loop.create_task(connect_nodes())


async def connect_nodes():
    await bot.wait_until_ready()
    wavelink.Node = wavelink.Node(uri='http://localhost:2333', password=wavelinkPassword)
    await wavelink.NodePool.connect(client=bot, nodes=[wavelink.Node])


@bot.event
async def on_wavelink_node_ready(node: wavelink.Node):
    print(f'{node} is ready!')


class TrollTools(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.target_channel_id = None
        self.description = 'Несколько глупых команд для троллинга'

    @commands.command(name='оплеуху', description='Введите: '
                                                  '"оплеуху @имя_жертвы@" чтобы "дать ему оплеуху"')
    async def slap(self, ctx):
        victim = ' '.join(ctx.message.content.split()[1:])
        res = victim + " " + random.choice(ways_of_delivery) + " " + "оплеуху от " + random.choice(slappers)
        if self.target_channel_id is not None:
            channel = bot.get_channel(self.target_channel_id)
        [await channel.send(res) if self.target_channel_id is not None else await ctx.send(res)]
        self.target_channel_id = None

    @commands.command(name='targetchat', description='Введите эту команду,'
                                                     ' чтобы определить чат,'
                                                     ' в который отправится следующая команда')
    async def target_chat(self, ctx):
        chatID = ' '.join(ctx.message.content.split()[1:])
        try:
            self.target_channel_id = int(chatID)
        except:
            pass


class CustomPlayer(wavelink.Player):

    def __init__(self):
        super().__init__()
        self.queue = wavelink.Queue()
        self.autoplay = True


class YoutubeMusic(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.description = 'Воспроизведение аудио с YoutTube'

    @commands.command(name='j', description='Введите эту команду,'
                                            ' чтобы присоединить бота к голосовому чату,'
                                            ' в котором вы находитесь')
    async def join(self, ctx):
        if ctx.author.voice is not None:
            try:
                await ctx.author.voice.channel.connect(cls=CustomPlayer())
            except discord.ClientException:
                await ctx.message.channel.send('Already in a channel')
        else:
            await ctx.message.channel.send('There is nobody in a channel')

    @commands.command(name='dc', description='Введите эту команду,'
                                             ' чтобы отсоединить бота от голосового чата')
    async def leave(self, ctx):
        vc = ctx.voice_client
        if vc:
            await vc.disconnect()
        else:
            await ctx.message.channel.send('I am not in a channel')

    @commands.command(name='p', description='Введите URL или название видео,'
                                            ' аудио которого проиграет бот')
    async def play(self, ctx):
        vc = ctx.voice_client
        song = ' '.join(ctx.message.content.split()[1:])
        print(song)
        if vc:
            if len(song) == 0:
                if vc.is_playing() and not vc.is_paused():
                    await vc.pause()
                elif vc.is_paused():
                    await vc.resume()
                else:

                    await ctx.message.channel.send('Enter song name or url for me to play it')
            else:
                track = await wavelink.YouTubeTrack.search(song, return_first=True)
                vc.queue.put(track)
                if not vc.is_playing():
                    await vc.play(vc.queue.get())
        else:
            await ctx.author.voice.channel.connect(cls=CustomPlayer())
            vc = ctx.voice_client
            if len(song) == 0:
                if vc.is_playing() and not vc.is_paused():
                    await vc.pause()
                elif vc.is_paused():
                    await vc.resume()
                else:
                    await ctx.message.channel.send('Enter song name or url for me to play it')
            else:
                track = await wavelink.YouTubeTrack.search(song, return_first=True)
                vc.queue.put(track)
                if not vc.is_playing():
                    await vc.play(vc.queue.get())

    @commands.command(name='pn', description='Введите эту команду,'
                                             ' чтобы заменить текущий трек')
    async def playNow(self, ctx):
        vc = ctx.voice_client
        if vc:
            song = ' '.join(ctx.message.content.split()[1:])
            if len(song) != 0:
                track = await wavelink.YouTubeTrack.search(song, return_first=True)
                await vc.play(track)
            else:
                await ctx.message.channel.send('Enter song name or url for me to play it')
        else:
            await ctx.author.voice.channel.connect(cls=CustomPlayer())
            vc = ctx.voice_client
            song = ' '.join(ctx.message.content.split()[1:])
            if len(song) != 0:
                track = await wavelink.YouTubeTrack.search(song, return_first=True)
                await vc.play(track)
            else:
                await ctx.message.channel.send('Enter song name or url for me to play it')

    @commands.command(name='s', description='Введите эту команду,'
                                            'чтобы пропустить текущий трек')
    async def skip(self, ctx):
        vc = ctx.voice_client
        if vc:
            if vc.is_playing() or vc.is_paused():
                try:
                    await vc.play(vc.queue.get())
                    await ctx.message.channel.send('Skipped!')
                except wavelink.QueueEmpty:
                    await ctx.message.channel.send('Queue is empty')
                    await vc.stop()
            else:
                await ctx.message.channel.send('Nothing is playing rn')
        else:
            await ctx.message.channel.send('I am not in a channel')

    @commands.command(name='v', description='Введите эту команду и после неё число от 0 до 1000,'
                                            ' чтобы установить необходимую громкость')
    async def volume(self, ctx):
        vc = ctx.voice_client
        vol = ctx.message.content.split()[1:]
        if vc:
            if len(vol) != 0:
                if vol[0].isdigit() and len(vol[0]) != 0 and (0 <= int(vol[0]) <= 1000):
                    await vc.set_volume(int(vol[0]))
                    await ctx.message.channel.send(f'Volume has been set to {vc.volume}!')
                else:
                    await ctx.message.channel.send('Enter a digit between 0 and 1000 to set a volume level')
            else:
                await ctx.message.channel.send('Enter a digit between 0 and 1000 to set a volume level')
        else:
            await ctx.message.channel.send('I am not in a channel')

    @commands.command(name='q', description='Введите эту команду,'
                                            ' чтобы вывести очередь в чат')
    async def showQueue(self, ctx):
        vc = ctx.voice_client
        if vc:
            toprint = ''
            toprint += f'Now playing:\n{vc.current}\n'
            try:
                q = vc.queue.copy()
                if len(q) != 0:
                    toprint += 'Queue:\n'
                    for i in range(len(q)):
                        toprint += f'{i + 1}. {q[i]}\n'
                    await ctx.message.channel.send(toprint)
                else:
                    if vc.current:
                        await ctx.message.channel.send(toprint)
                    await ctx.message.channel.send('Queue is empty')
            except wavelink.QueueEmpty:
                await ctx.message.channel.send('Queue is empty')
        else:
            await ctx.message.channel.send('I am not in a channel')

    @commands.command(name='c', description='Введите эту команду,'
                                            'чтобы показать подробную информацию о треке')
    async def currentTrack(self, ctx):
        vc = ctx.voice_client
        if vc:
            if vc.current:
                await ctx.message.channel.send(vc.current)
                await ctx.message.channel.send(vc.current.thumbnail)
            else:
                await ctx.message.channel.send('Nothing is playing rn')
        else:
            await ctx.message.channel.send('I am not in a channel')

    @commands.command(name='l', description='Включить/Выключить'
                                            ' повторение текущего трека')
    async def loop(self, ctx):
        vc = ctx.voice_client
        if vc:
            if vc.is_playing():
                if vc.queue.loop:
                    vc.queue.loop = False
                    await ctx.message.channel.send('Un-looped!')
                else:
                    vc.queue.loop = True
                    await ctx.message.channel.send('Looped!')
            else:
                await ctx.message.channel.send('Nothing is playing rn')
        else:
            await ctx.message.channel.send('I am not in a channel')


@bot.event
async def on_message(message):
    if message.author.id != bot.application_id:
        if 'fumo' in message.content.lower() or 'фумо' in message.content.lower():
            r = requests.get(
                "https://tenor.googleapis.com/v2/search?q=%s&key=%s&client_key=%s&limit=%s" % (
                    "фумо", 'AIzaSyBFqfN9tVHa6bJ537O-J3mcWL4E8jnfMnw', 'Beninger1', 1000)).json()['results']
            await message.channel.send(random.choice(r)['media_formats']['gif']['url'])
        elif 'pep' in message.content.lower() or 'пеп' in message.content.lower():
            r = requests.get(
                "https://tenor.googleapis.com/v2/search?q=%s&key=%s&client_key=%s&limit=%s" % (
                    "pepe", 'AIzaSyBFqfN9tVHa6bJ537O-J3mcWL4E8jnfMnw', 'Beninger1', 1000)).json()['results']
            await message.channel.send(random.choice(r)['media_formats']['gif']['url'])
    await bot.process_commands(message)


async def main():
    await bot.add_cog(TrollTools(bot))
    await bot.add_cog(YoutubeMusic(bot))
    await bot.start(TOKEN)


asyncio.run(main())
