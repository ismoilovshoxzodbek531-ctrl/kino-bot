import asyncio
import sqlite3
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage

# --- SOZLAMALAR ---
# Tokenni yana bir bor tekshirib ko'ring
BOT_TOKEN = "8686458756:AAHJgeuDxLn9-tl8TiXYa-yJ7cJ-dejt_Pc"

# Logging (Xatolarni ko'rish uchun)
logging.basicConfig(level=logging.INFO)

# RENDERDA PROXY KERAK EMAS - Shunchaki Botni o'zini ulaymiz
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Baza yaratish
def init_db():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS movies (code TEXT UNIQUE, file_id TEXT)')
    conn.commit()
    conn.close()

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("Salom! Kino kodini yuboring.")

@dp.message(F.text)
async def get_movie(message: Message):
    # Agar xabar raqam yoki kod bo'lsa bazadan qidiradi
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT file_id FROM movies WHERE code = ?', (message.text,))
    res = cursor.fetchone()
    conn.close()
    
    if res:
        await message.answer_video(res[0])
    else:
        await message.answer("Kino topilmadi. Kodni to'g'ri yozganingizga ishonch hosil qiling.")

async def main():
    init_db()
    logging.info("Bot ishga tushmoqda...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi")
