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
BOT_TOKEN = "8686458756:AAHWAnDQcUR_0Bg9iMLk0eZbq_C0s4b_sXA"
ADMIN_ID = 591146270  # <--- SHU YERGA O'ZINGIZNI ID RAQAMINGIZNI YOZING!

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class AdminStates(StatesGroup):
    waiting_for_ad = State()

# --- WEB SERVER (Render uchun) ---
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
    cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER UNIQUE)')
    conn.commit()
    conn.close()

# --- ADMIN TUGMALARI ---
def get_admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Reklama yuborish", callback_query_id="send_ad")],
        [InlineKeyboardButton(text="📊 Statistika", callback_query_id="stats")]
    ])

# --- HANDLERS ---
@dp.message(CommandStart())
async def start(message: Message):
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (message.from_user.id,))
    conn.commit()
    conn.close()
    
    txt = "Salom! Kino kodini yuboring."
    if message.from_user.id == ADMIN_ID:
        txt += "\n\nSiz adminsiz! Panelni ko'rish uchun /admin yozing."
    await message.answer(txt)

@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Admin panelga xush kelibsiz:", reply_markup=get_admin_kb())
    else:
        await message.answer("Kechirasiz, siz admin emassiz.")

@dp.callback_query(F.data == "send_ad")
async def ad_start(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Reklama xabarini yuboring (Rasm yoki matn):")
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
                await message.answer(f"✅ Kino saqlandi! Kod: {code}")
            except:
                await message.answer("❌ Bu kod bazada bor.")
            conn.close()
        else:
            await message.answer("⚠️ Videoga izoh (caption) qilib kod yozing!")

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
        await message.answer("🔍 Kino topilmadi.")

async def main():
    init_db()
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
