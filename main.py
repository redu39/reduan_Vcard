import asyncio, logging, sqlite3, os, sys
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramNetworkError

# ================= CONFIG =================
import os

TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "5001039092"))

db = sqlite3.connect("raftaar_final_master.db", check_same_thread=False)
cur = db.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS gallery (id INTEGER PRIMARY KEY AUTOINCREMENT, file_id TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS socials (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, url TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS phones (id INTEGER PRIMARY KEY AUTOINCREMENT, number TEXT)")
db.commit()

# প্রাথমিক ডাটা সেটআপ
cur.execute("SELECT COUNT(*) FROM phones")
if cur.fetchone()[0] == 0:
    cur.executemany("INSERT INTO phones (number) VALUES (?)", [("01642425537",), ("01988338696",)])
    cur.executemany("INSERT INTO socials (name, url) VALUES (?, ?)", [
        ("WhatsApp", "https://wa.me/8801642425537"),
        ("Facebook", "https://www.facebook.com/share/1LKGsbohSo/"),
        ("Instagram", "https://www.instagram.com/3rd_person_ridu?igsh=cTI5ZGFsdnM1N3B6"),
        ("TikTok", "https://www.tiktok.com/@raftaarrdn")
    ])
    welcome_msg = "👀 Curious about me?\nYou’re in the right place!\nThis bot is my all-in-one digital identity.\n👉 Tap below and discover more."
    cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('welcome', ?)", (welcome_msg,))
    cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('email', 'reduanislam7411@gmail.com')")
    db.commit()

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

class AdminStates(StatesGroup):
    waiting_photo = State()
    waiting_cv = State()
    edit_social_url = State()
    add_phone = State()
    edit_phone = State()
    waiting_bc = State()

# ================= KEYBOARD =================
def main_kb():
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="📞 Contact", callback_data="contact"),
           types.InlineKeyboardButton(text="📧 Email", callback_data="email"))
    kb.row(types.InlineKeyboardButton(text="🖼 Photo Gallery", callback_data="gal_0"))
    kb.row(types.InlineKeyboardButton(text="📄 Resume / CV", callback_data="cv"))
    kb.row(types.InlineKeyboardButton(text="🌐 Social Media", callback_data="social"))
    kb.row(types.InlineKeyboardButton(text="📥 Save Contact", callback_data="save"))
    return kb.as_markup()

def admin_kb():
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="📊 Stats", callback_data="adm_stats"),
           types.InlineKeyboardButton(text="🖼 Add Photo", callback_data="adm_addpic"))
    kb.row(types.InlineKeyboardButton(text="📄 Update CV", callback_data="adm_upcv"),
           types.InlineKeyboardButton(text="📢 Broadcast", callback_data="adm_bc"))
    kb.row(types.InlineKeyboardButton(text="⚙️ Edit Socials", callback_data="adm_soc"),
           types.InlineKeyboardButton(text="📞 Manage Phones", callback_data="adm_phn"))
    # ইউজার মুডে ফেরার বাটন
    kb.row(types.InlineKeyboardButton(text="⬅️ Back to User Mode", callback_data="main"))
    return kb.as_markup()

# ================= HANDLERS =================
@dp.message(Command("start"))
async def start(m: types.Message):
    cur.execute("INSERT OR IGNORE INTO users (id, name) VALUES (?, ?)", (m.from_user.id, m.from_user.full_name))
    db.commit()
    cur.execute("SELECT value FROM settings WHERE key='welcome'")
    txt = cur.fetchone()[0]
    await m.answer(f"<b>Raftaar Reduan</b>\n\n{txt}", reply_markup=main_kb())

@dp.callback_query(F.data == "main")
async def back_to_main(c: types.CallbackQuery):
    cur.execute("SELECT value FROM settings WHERE key='welcome'")
    txt = cur.fetchone()[0]
    await c.message.edit_text(f"<b>Raftaar Reduan</b>\n\n{txt}", reply_markup=main_kb())
    await c.answer()

@dp.callback_query(F.data == "contact")
async def contact(c: types.CallbackQuery):
    cur.execute("SELECT number FROM phones")
    nums = cur.fetchall()
    txt = "<b>📱 My Contact Numbers:</b>\n\n" + "\n".join([f"• <code>{n[0]}</code>" for n in nums])
    kb = InlineKeyboardBuilder().add(types.InlineKeyboardButton(text="Back", callback_data="main"))
    await c.message.edit_text(txt, reply_markup=kb.as_markup())
    await c.answer()

@dp.callback_query(F.data == "email")
async def email(c: types.CallbackQuery):
    cur.execute("SELECT value FROM settings WHERE key='email'")
    e = cur.fetchone()[0]
    kb = InlineKeyboardBuilder().add(types.InlineKeyboardButton(text="Back", callback_data="main"))
    await c.message.edit_text(f"📧 <b>My Email:</b>\n<code>{e}</code>", reply_markup=kb.as_markup())
    await c.answer()

@dp.callback_query(F.data == "social")
async def social(c: types.CallbackQuery):
    cur.execute("SELECT name, url FROM socials")
    links = cur.fetchall()
    kb = InlineKeyboardBuilder()
    for n, u in links: kb.row(types.InlineKeyboardButton(text=n, url=u))
    kb.row(types.InlineKeyboardButton(text="Back", callback_data="main"))
    await c.message.edit_text("🔗 <b>Social Identity:</b>", reply_markup=kb.as_markup())
    await c.answer()

@dp.callback_query(F.data.startswith("gal_"))
async def gallery(c: types.CallbackQuery):
    i = int(c.data.split("_")[1])
    cur.execute("SELECT file_id, id FROM gallery")
    pics = cur.fetchall()
    if not pics: return await c.answer("Gallery is empty!", show_alert=True)
    
    kb = InlineKeyboardBuilder()
    if i > 0: kb.add(types.InlineKeyboardButton(text="⬅️ Prev", callback_data=f"gal_{i-1}"))
    if i < len(pics)-1: kb.add(types.InlineKeyboardButton(text="Next ➡️", callback_data=f"gal_{i+1}"))
    kb.row(types.InlineKeyboardButton(text="Back to Menu", callback_data="main_del"))
    if c.from_user.id == ADMIN_ID:
        kb.row(types.InlineKeyboardButton(text="🗑 Delete Photo", callback_data=f"delp_{pics[i][1]}"))
    
    media = types.InputMediaPhoto(media=pics[i][0], caption=f"Photo {i+1}/{len(pics)}")
    try:
        if c.message.photo: await c.message.edit_media(media=media, reply_markup=kb.as_markup())
        else:
            await c.message.delete()
            await c.message.answer_photo(pics[i][0], caption=media.caption, reply_markup=kb.as_markup())
    except: await c.answer("Loading...")
    await c.answer()

@dp.callback_query(F.data == "main_del")
async def main_del(c: types.CallbackQuery):
    await c.message.delete()
    await start(c.message)

@dp.callback_query(F.data == "cv")
async def get_cv(c: types.CallbackQuery):
    cur.execute("SELECT value FROM settings WHERE key='cv_id'")
    res = cur.fetchone()
    if res: await c.message.answer_document(res[0], caption="📄 My Resume")
    else: await c.answer("CV not uploaded!", show_alert=True)
    await c.answer()

# ================= ADMIN HANDLERS =================
@dp.message(Command("admin"))
async def admin(m: types.Message):
    if m.from_user.id == ADMIN_ID:
        await m.answer("🛠 <b>Admin Dashboard</b>", reply_markup=admin_kb())

@dp.callback_query(F.data == "adm_stats")
async def stats(c: types.CallbackQuery):
    cur.execute("SELECT COUNT(*) FROM users")
    count = cur.fetchone()[0]
    await c.message.answer(f"📊 Total Users: {count}")
    await c.answer()

@dp.callback_query(F.data == "adm_addpic")
async def addpic(c: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_photo)
    await c.message.answer("📸 Send Photo:")
    await c.answer()

@dp.message(AdminStates.waiting_photo, F.photo)
async def addpic_done(m: types.Message, state: FSMContext):
    cur.execute("INSERT INTO gallery (file_id) VALUES (?)", (m.photo[-1].file_id,))
    db.commit()
    await state.clear()
    await m.answer("✅ Photo Added!", reply_markup=admin_kb())

@dp.callback_query(F.data == "adm_bc")
async def broadcast_start(c: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_bc)
    await c.message.answer("📢 Send message for broadcast:")
    await c.answer()

@dp.message(AdminStates.waiting_bc)
async def broadcast_done(m: types.Message, state: FSMContext):
    cur.execute("SELECT id FROM users")
    users = cur.fetchall()
    sent = 0
    for u in users:
        try:
            await bot.send_message(u[0], f"📢 <b>Update:</b>\n\n{m.text}")
            sent += 1
            await asyncio.sleep(0.05)
        except: pass
    await state.clear()
    await m.answer(f"✅ Sent to {sent} users.", reply_markup=admin_kb())

@dp.callback_query(F.data == "save")
async def save_vcf(c: types.CallbackQuery):
    cur.execute("SELECT number FROM phones")
    n = cur.fetchall()
    vcard = f"BEGIN:VCARD\nVERSION:3.0\nFN:Raftaar Reduan\nTEL;TYPE=CELL:{n[0][0] if n else ''}\nEND:VCARD"
    with open("Raftaar.vcf", "w") as f: f.write(vcard)
    await c.message.answer_document(types.FSInputFile("Raftaar.vcf"))
    await c.answer()

# ================= RUNNER WITH RECONNECT =================
async def main():
    while True:
        try:
            print("🚀 Raftaar Reduan Bot is Starting...")
            await bot.delete_webhook(drop_pending_updates=True)
            await dp.start_polling(bot)
        except TelegramNetworkError:
            print("📡 Connection lost. Retrying in 10s...")
            await asyncio.sleep(10)
        except Exception as e:
            print(f"❌ Error: {e}")
            await asyncio.sleep(10)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass