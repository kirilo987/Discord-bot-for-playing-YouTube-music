import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
import yt_dlp as youtube_dl
import asyncio
import os

#####################################################
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=">", intents=intents)
#####################################################
#    СТОП. В майбутньому тут будуть тех команди     #
@bot.command(name='stop')
@commands.is_owner()
async def stop(ctx):
 await bot.close()

######################
#Налаштування yt-dlp #
######################
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'options': '-vn'
}
###############################
#    Музикова частина         #
###############################
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=1.0):
        super().__init__(source, volume)

        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

@bot.command(name='join')
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
    else:
        await ctx.send("Ви повинні бути у голосовому каналі, щоб використати цю команду.")

@bot.command(name='play')
async def play(ctx, url):
    if ctx.voice_client is None:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("Ви повинні бути у голосовому каналі, щоб використати цю команду.")
            return

    try:
        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
            await ctx.send(f'Відтворюється: {player.title}')
    except Exception as e:
        await ctx.send(f"Сталася помилка: {e}")

@bot.command(name='lplay')
async def lplay(ctx, *, filename: str):
    if ctx.voice_client is None:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("Ви повинні бути у голосовому каналі, щоб використати цю команду.")
            return

    file_path = os.path.join("local", f"{filename}.mp3")

    if not os.path.isfile(file_path):
        await ctx.send(f"Файл {filename}.mp3 не знайдено в папці 'local'.")
        return

    try:
        ctx.voice_client.stop() 
        source = FFmpegPCMAudio(file_path)
        ctx.voice_client.play(source, after=lambda e: print(f'Player error: {e}') if e else None)
    except Exception as e:
        await ctx.send(f"Сталася помилка при відтворенні файлу: {e}")

@bot.command(name='pause')
async def pause(ctx):
    if ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("Музику зупинено.")
    else:
        await ctx.send("Наразі нічого не відтворюється.")

@bot.command(name='resume')
async def resume(ctx):
    if ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("Музику відновлено.")
    else:
        await ctx.send("Музику не на паузі.")

@bot.command(name='stopm')
async def stopm(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()
        await ctx.send("Відтворення музики зупинено.")
    else:
        await ctx.send("Бот не у голосовому каналі.")

@bot.command(name='leave')
async def l(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Бот залишив голосовий канал.")
    else:
        await ctx.send("Бот не у голосовому каналі.")

#####################################################
# Соціал кредит часть чина короче
#####################################################
# Шлях до файлів для зберігання даних
credit_file = './Social credit/Social_credit.txt'
log_file = './Social credit/Social_credit_logs.log'

# Функція для зміни соціального кредиту
def change_social_credit(user_id: int, amount: int, reason: str):
    # Читання поточного стану кредитів
    try:
        with open(credit_file, 'r') as f:
            credits = {line.split('|')[0]: int(line.split('|')[1].strip()) for line in f}
    except FileNotFoundError:
        credits = {}

    # Зміна кредиту
    current_credit = credits.get(str(user_id), 0)
    new_credit = current_credit + amount
    credits[str(user_id)] = new_credit

    # Запис нового стану кредитів
    with open(credit_file, 'w') as f:
        for uid, credit in credits.items():
            f.write(f'{uid}|{credit}\n')

    # Запис у лог
    with open(log_file, 'a') as f:
        f.write(f'User: {user_id} | Change: {amount} | New Credit: {new_credit} | Reason: {reason}\n')

    return new_credit

# Команда для зміни соціального кредиту
@bot.command(name='credit')
async def social_credit(ctx, action: str, amount: int, member: discord.Member, *, reason: str):
    if action not in ['+', '-']:
        await ctx.send('Використовуйте "+" або "-" для зміни соціального кредиту.')
        return

    amount = amount if action == '+' else -amount
    new_credit = change_social_credit(member.id, amount, reason)
    await ctx.send(f'Соціальний кредит {member.mention} змінено на {amount}. Новий кредит: {new_credit}. Причина: {reason}')

#####################################################
# Шось буде)))
#####################################################

bot.run('YOU TOKEN')
