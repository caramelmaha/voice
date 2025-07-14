from pytz import timezone
from datetime import datetime
import discord
from discord.ext import commands, tasks
import yt_dlp
import asyncio

TOKEN = 
VC_CHANNEL_ID = 1371799741066776728  # ห้องเสียงที่จะเข้าทุกวัน
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 🗓️ เวลาที่ต้องเล่นเสียง "ทุกวัน"
SCHEDULES = [
    {"hour":  0,  "minute": 55,"url": "https://www.youtube.com/watch?v=gbvGlZh7BdI"},
    {"hour":  2,  "minute": 55,"url": "https://www.youtube.com/watch?v=umHdZ6hTGdg"},
    {"hour":  3,  "minute": 55,"url": "https://www.youtube.com/watch?v=gbvGlZh7BdI"},
    {"hour":  18, "minute": 55,"url": "https://www.youtube.com/watch?v=umHdZ6hTGdg"},
    {"hour":  19, "minute": 55,"url": "https://www.youtube.com/watch?v=gbvGlZh7BdI"},
]

# ใช้ list เก็บ timestamp ที่เล่นไปแล้ว เพื่อกันไม่ให้ยิงซ้ำภายในรอบเดียว
played_today = set()

@bot.event
async def on_ready():
    print(f'✅ บอทออนไลน์: {bot.user}')
    scheduled_play.start()

async def play_audio(channel, url):
    vc = await channel.connect()

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        audio_url = info['url']

    ffmpeg_options = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
    }

    def after_playing(error):
        coro = vc.disconnect()
        fut = asyncio.run_coroutine_threadsafe(coro, bot.loop)
        fut.result()

    vc.play(discord.FFmpegPCMAudio(audio_url, **ffmpeg_options), after=after_playing)

@tasks.loop(minutes=1)
async def scheduled_play():
    now = datetime.now(timezone("Asia/Bangkok"))
    current_tag = f"{now.hour}:{now.minute}"

    # Reset played list ทุกวันเวลา 00:00
    if current_tag == "0:0":
        played_today.clear()

    for schedule in SCHEDULES:
        schedule_tag = f"{schedule['hour']}:{schedule['minute']}"
        if current_tag == schedule_tag and schedule_tag not in played_today:
            print(f"▶️ {now.strftime('%H:%M')} - Playing: {schedule['url']}")
            played_today.add(schedule_tag)
            channel = bot.get_channel(VC_CHANNEL_ID)
            if channel:
                await play_audio(channel, schedule["url"])

@bot.command(name="testz")
async def test_command(ctx):
    """เล่นคลิปล่าสุดจาก SCHEDULES เพื่อทดสอบ"""
    channel = bot.get_channel(VC_CHANNEL_ID)
    if channel:
        await play_audio(channel, SCHEDULES[0]["url"])
        await ctx.send("✅ กำลังเล่นทดสอบรอบแรกในตาราง")
    else:
        await ctx.send("❌ ไม่เจอห้องเสียง")

bot.run(TOKEN)
