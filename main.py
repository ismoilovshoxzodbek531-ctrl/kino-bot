import asyncio
import logging
import sqlite3
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart

# --- SOZLAMALAR ---
# Tokeningizni tekshirib ko'ring, u qo'shtirnoq ichida bo'lishi shart
BOT_TOKEN = "8686458756:AAHWANdQcUR_0Bg9iMLk0eZbq_C0s4b_sXA"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- WEB SERVER (Render botni o'chirib qo'ymasligi uchun) ---
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 10000)))
    await site.start()

# --- BAZA ---
def init_db():
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS movies (code TEXT UNIQUE, file_id TEXT)')
    conn.commit()
    conn.close()

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("Salom! Bot Render-da ishladi. Kino kodini yuboring.")

@dp.message(F.text)
async def get_movie(message: Message):
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT file_id FROM movies WHERE code = ?', (message.text,))
    res = cursor.fetchone()
    conn.close()
    if res:
        await message.answer_video(res[0])
    else:
        await message.answer("Kino topilmadi.")

async def main():
    init_db()
    await start_web_server() # Web serverni yurgizamiz
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
