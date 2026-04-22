import asyncio
import sqlite3
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart

# TOKENNI TO'G'RI YOZING
BOT_TOKEN = "8686458756:AAHJgeuDxLn9-tl8TiXYa-yJ7cJ-dejt_Pc"

logging.basicConfig(level=logging.INFO)

# Render uchun oddiy ulanish (Proxy-siz)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def init_db():
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS movies (code TEXT UNIQUE, file_id TEXT)')
    conn.commit()
    conn.close()

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("Salom! Bot Render-da muvaffaqiyatli ishga tushdi. Kino kodini yuboring.")

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
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
