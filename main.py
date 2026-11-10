import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

queues = {}
voice_clients = {}

YTDL_OPTS = {
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
FFMPEG_OPTS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} - Mochi is ready!')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="!play"))

async def play_next(ctx):
    guild_id = ctx.guild.id
    if queues.get(guild_id):
        url = queues[guild_id].pop(0)
        await play_url(ctx, url)
    else:
        await ctx.send("Queue ကုန်သွားပြီ ✨")

async def play_url(ctx, url):
    guild_id = ctx.guild.id
    vc = voice_clients.get(guild_id)
    with yt_dlp.YoutubeDL(YTDL_OPTS) as ydl:
        info = ydl.extract_info(url, download=False)
        if 'entries' in info:
            info = info['entries'][0]
        audio_url = info['url']
        title = info.get('title', 'Unknown')
    source = discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTS)
    def after(e):
        asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
    vc.play(source, after=after)
    await ctx.send(f'🎵 ဖွင့်နေပြီ: **{title}**')

@bot.command()
async def play(ctx, *, search: str):
    if not ctx.author.voice:
        await ctx.send("အရင် Voice Channel ထဲ ဝင်ပေးနော်!")
        return
    channel = ctx.author.voice.channel
    guild_id = ctx.guild.id
    vc = voice_clients.get(guild_id)
    if not vc:
        vc = await channel.connect()
        voice_clients[guild_id] = vc
    elif vc.channel != channel:
        await vc.move_to(channel)
    with yt_dlp.YoutubeDL(YTDL_OPTS) as ydl:
        info = ydl.extract_info(f"ytsearch:{search}", download=False)
        if 'entries' in info and info['entries']:
            url = info['entries'][0]['webpage_url']
        else:
            url = search
    if vc.is_playing():
        queues.setdefault(guild_id, []).append(url)
        await ctx.send(f"Queue ထဲ ထည့်လိုက်ပြီ: {search}")
    else:
        await play_url(ctx, url)

@bot.command()
async def skip(ctx):
    vc = voice_clients.get(ctx.guild.id)
    if vc and vc.is_playing():
        vc.stop()
        await ctx.send("⏭️ ကျော်လိုက်ပြီ")
    else:
        await ctx.send("ဘာမှ ဖွင့်မနေဘူး")

@bot.command()
async def stop(ctx):
    guild_id = ctx.guild.id
    vc = voice_clients.get(guild_id)
    if vc:
        queues[guild_id] = []
        await vc.disconnect()
        del voice_clients[guild_id]
        await ctx.send("🛑 ရပ်လိုက်ပြီ")
    else:
        await ctx.send("Voice ထဲ မရှိဘူး")

@bot.command()
async def queue(ctx):
    q = queues.get(ctx.guild.id, [])
    if not q:
        await ctx.send("Queue ထဲမှာ ဘာမှ မရှိဘူး")
    else:
        await ctx.send("\n".join([f"{i+1}. {u}" for i, u in enumerate(q)]))

@bot.command()
async def mochi(ctx):
    await ctx.send("ဟိုင်း! ငါက Mochi 🎀 !play [သီချင်းနာမည်] လို့ ရိုက်ပြီး သီချင်းဖွင့်လို့ရတယ်!")

bot.run(os.getenv("DISCORD_TOKEN"))
