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
BOT_TOKEN = "8686458756:AAHJgeuDxLn9-tl8TiXYa-yJ7cJ-dejt_Pc"
ADMIN_ID = 6848247065  

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- FSM (Holatlar) ---
class AdminStates(StatesGroup):
    waiting_for_ad = State()
    waiting_for_channel_link = State()
    waiting_for_channel_id = State()

# --- WEB SERVER ---
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
    cursor.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT UNIQUE, value TEXT)')
    # Boshlang'ich sozlamalar
    cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES ("channel_link", "https://t.me/your_channel")')
    cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES ("channel_id", "-100123456789")')
    conn.commit()
    conn.close()

def get_setting(key):
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else None

# --- MAJBURIY OBUNA TEKSHIRISH ---
async def check_sub(user_id):
    c_id = get_setting("channel_id")
    try:
        member = await bot.get_chat_member(chat_id=c_id, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return True # Xatolik bo'lsa o'tkazib yuboradi

# --- ADMIN PANEL TUGMALARI ---
def admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Reklama tarqatish", callback_query_id="send_ad")],
        [InlineKeyboardButton(text="🔗 Kanalni sozlash", callback_query_id="set_channel")],
        [InlineKeyboardButton(text="📊 Statistika", callback_query_id="stats")]
    ])

# --- HANDLERS ---
@dp.message(CommandStart())
async def start(message: Message):
    # Foydalanuvchini bazaga qo'shish
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (message.from_user.id,))
    conn.commit()
    conn.close()
    
    if not await check_sub(message.from_user.id):
        link = get_setting("channel_link")
        btn = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="A'zo bo'lish", url=link)]])
        return await message.answer("Botingizdan foydalanish uchun kanalimizga a'zo bo'ling!", reply_markup=btn)
    
    await message.answer("Salom! Kino kodini yuboring.")

@dp.message(Command("admin"), F.from_user.id == ADMIN_ID)
async def admin_menu(message: Message):
    await message.answer("Admin panel:", reply_markup=admin_keyboard())

# --- CALLBACKS ---
@dp.callback_query(F.data == "set_channel")
async def set_channel_start(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Kanalning to'liq linkini yuboring (masalan: https://t.me/uz_kinolar):")
    await state.set_state(AdminStates.waiting_for_channel_link)

@dp.message(AdminStates.waiting_for_channel_link)
async def save_link(message: Message, state: FSMContext):
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE settings SET value = ? WHERE key = "channel_link"', (message.text,))
    conn.commit()
    conn.close()
    await message.answer("Endi kanal ID raqamini yuboring (masalan: -100...):")
    await state.set_state(AdminStates.waiting_for_channel_id)

@dp.message(AdminStates.waiting_for_channel_id)
async def save_id(message: Message, state: FSMContext):
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE settings SET value = ? WHERE key = "channel_id"', (message.text,))
    conn.commit()
    conn.close()
    await message.answer("✅ Kanal sozlamalari saqlandi!")
    await state.clear()

@dp.callback_query(F.data == "send_ad")
async def ad_start(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Reklama xabarini yuboring (Rasm, matn yoki video):")
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
            await asyncio.sleep(0.05) # Bloklanmaslik uchun
        except: pass
    
    await message.answer(f"✅ Reklama {count} ta foydalanuvchiga yuborildi.")
    await state.clear()

# --- KINO QIDIRISH ---
@dp.message(F.text)
async def get_movie(message: Message):
    if not await check_sub(message.from_user.id):
        return await message.answer("Avval kanalga a'zo bo'ling!")
        
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
