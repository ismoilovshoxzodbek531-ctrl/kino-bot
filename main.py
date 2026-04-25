import asyncio
import logging
import sqlite3
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# --- SOZLAMALAR ---
# O'zingizning yangi tokeningizni qo'ying
BOT_TOKEN = "8686458756:AAHJgeuDxLn9-tl8TiXYa-yJ7cJ-dejt_Pc"
ADMIN_ID = 6848247065  

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class AdminStates(StatesGroup):
    waiting_for_ad = State()

async def handle(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 10000)))
    await site.start()

def init_db():
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS movies (code TEXT UNIQUE, file_id TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER UNIQUE)')
    conn.commit()
    conn.close()

@dp.message(CommandStart())
async def start(message: Message):
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (message.from_user.id,))
    conn.commit()
    conn.close()
    await message.answer("Salom! Kino kodini yuboring yoki admin bo'lsangiz /admin yozing.")

@dp.message(Command("admin"), F.from_user.id == ADMIN_ID)
async def admin_panel(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Reklama yuborish", callback_query_id="send_ad")]
    ])
    await message.answer("Admin panel:", reply_markup=kb)

@dp.callback_query(F.data == "send_ad")
async def ad_start(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Reklama xabarini (rasm/matn) yuboring:")
    await state.set_state(AdminStates.waiting_for_ad)

@dp.message(AdminStates.waiting_for_ad)
async def broadcast_ad(message: Message, state: FSMContext):
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users')
    users = cursor.fetchall()
    conn.close()
    
    count = 0
    for user in users:
        try:
            await message.copy_to(chat_id=user[0])
            count += 1
            await asyncio.sleep(0.05)
        except: pass
    await message.answer(f"✅ Reklama {count} kishiga yuborildi.")
    await state.clear()

@dp.message(F.video)
async def add_movie(message: Message):
    if message.from_user.id == ADMIN_ID:
        code = message.caption
        if code:
            file_id = message.video.file_id
            conn = sqlite3.connect('bot.db')
            cursor = conn.cursor()
            try:
                cursor.execute('INSERT INTO movies (code, file_id) VALUES (?, ?)', (code, file_id))
                conn.commit()
                await message.answer(f"✅ Kino qo'shildi: {code}")
            except: await message.answer("❌ Xato yoki bu kod band.")
            conn.close()
        else: await message.answer("⚠️ Video ostiga kodni yozing!")

@dp.message(F.text)
async def get_movie(message: Message):
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT file_id FROM movies WHERE code = ?', (message.text,))
    res = cursor.fetchone()
    conn.close()
    if res: await message.answer_video(res[0])
    else: await message.answer("🔍 Kino topilmadi.")

async def main():
    init_db()
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
