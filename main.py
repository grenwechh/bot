import os, sqlite3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
TOKEN=os.environ.get("TELEGRAM_BOT_TOKEN")
ADMIN_ID=8817751663
ADMIN_USERNAME="fizaccountss"
CRYPTO_LINK="https://app.tonkeeper.com/transfer/UQBDCGe7u3V-3T-dSNbaGBP6brOVoWc_Vnp1q_bUapQOs3A_"
TON_LINK="https://staffov-king.ton"
conn=sqlite3.connect("shop.db", check_same_thread=False)
cur=conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0)")
cur.execute("CREATE TABLE IF NOT EXISTS numbers (id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT, name TEXT, price INTEGER, emoji TEXT)")
conn.commit()
START=[("RU","Россия",195,"🇷🇺"),("CO","Колумбия",40,"🇨🇴"),("ID","Индонезия",46,"🇮🇩"),("KE","Кения",43,"🇰🇪"),("IR","Иран",57,"🇮🇷"),("AF","Афганистан",61,"🇦🇫"),("MM","Мьянма",62,"🇲🇲"),("CL","Чили",62,"🇨🇱"),("MA","Марокко",65,"🇲🇦"),("BD","Бангладеш",65,"🇧🇩")]
def init():
    cur.execute("SELECT COUNT(*) FROM numbers")
    if cur.fetchone()[0]==0:
        for c,n,p,e in START:
            cur.execute("INSERT INTO numbers (code,name,price,emoji) VALUES (?,?,?,?)",(c,n,p,e))
        conn.commit()
init()
def is_admin(uid): return uid==ADMIN_ID
async def show_main(update, context, edit=False):
    uid=update.effective_user.id
    cur.execute("INSERT OR IGNORE INTO users (id) VALUES (?)",(uid,)); conn.commit()
    text="• Приветствуем тебя!\n\nСервис для покупки номеров. Сначала идут самые дешевые!"
    kb=[[InlineKeyboardButton("📱 Купить номер", callback_data="countries_0")],[InlineKeyboardButton("👤 Профиль", callback_data="profile")],[InlineKeyboardButton("💳 Пополнить баланс", callback_data="balance")]]
    if is_admin(uid): kb.append([InlineKeyboardButton("🔧 Админ-панель", callback_data="admin")])
    markup=InlineKeyboardMarkup(kb)
    photo="https://i.imgur.com/8Km9tLL.png"
    q=update.callback_query
    if edit and q:
        try: await q.message.delete()
        except: pass
        await context.bot.send_photo(uid, photo, caption=text, reply_markup=markup)
        await q.answer()
    else:
        await context.bot.send_photo(update.effective_chat.id, photo, caption=text, reply_markup=markup)
async def show_countries(update, context):
    q=update.callback_query
    cur.execute("SELECT code,name,price,emoji FROM numbers ORDER BY price ASC")
    all_c=cur.fetchall()
    kb=[];ru=next((c for c in all_c if c[0]=='RU'),None)
    if ru: kb.append([InlineKeyboardButton(f"{ru[3]} {ru[1]} • {ru[2]}₽", callback_data=f"buy_{ru[0]}")])
    row=[]
    for code,name,price,emoji in all_c:
        if code=='RU': continue
        row.append(InlineKeyboardButton(f"{emoji} {name} • {price}₽", callback_data=f"buy_{code}"))
        if len(row)==2: kb.append(row); row=[]
    if row: kb.append(row)
    kb.append([InlineKeyboardButton("⬅️ Назад", callback_data="menu")])
    await q.message.delete()
    await context.bot.send_message(q.from_user.id, "🌐 Страны\nСначала идут самые дешевые!", reply_markup=InlineKeyboardMarkup(kb))
    await q.answer()
async def handle_buttons(update, context):
    q=update.callback_query;data=q.data;uid=q.from_user.id;user=update.effective_user;user_tag=f"@{user.username}" if user.username else f"ID {user.id}"
    if data=="menu": await show_main(update, context, True)
    elif data.startswith("countries_"): await show_countries(update, context)
    elif data.startswith("buy_"): await q.answer("Пополни баланс сначала", show_alert=True)
    elif data=="profile":
        cur.execute("SELECT balance FROM users WHERE id=?",(uid,));bal=cur.fetchone()[0]
        await q.answer(f"Юз: {user_tag}\nБаланс: {bal}₽", show_alert=True)
    elif data=="balance":
        kb=[[InlineKeyboardButton("💎 CryptoBot", callback_data="pay_crypto")],[InlineKeyboardButton("💎 Tonkeeper", callback_data="pay_ton")],[InlineKeyboardButton("⬅️ Назад", callback_data="menu")]]
        await q.message.delete();await context.bot.send_message(uid, "💳 Выбери способ оплаты:", reply_markup=InlineKeyboardMarkup(kb));await q.answer()
    elif data=="pay_crypto":
        try: await context.bot.send_message(ADMIN_ID, f"💎 ЗАЯВКА CryptoBot\n👤 {user_tag}\nID: {uid}")
        except: pass
        kb=[[InlineKeyboardButton("💸 Оплатить", url=CRYPTO_LINK)],[InlineKeyboardButton("💬 Админ", url=f"https://t.me/{ADMIN_USERNAME}")],[InlineKeyboardButton("⬅️ Назад", callback_data="menu")]]
        await q.message.delete();await context.bot.send_message(uid, f"💳 Оплати:\n{CRYPTO_LINK}\nСкинь чек админу.", reply_markup=InlineKeyboardMarkup(kb));await q.answer()
    elif data=="pay_ton":
        try: await context.bot.send_message(ADMIN_ID, f"💎 ЗАЯВКА TON\n👤 {user_tag}\nID: {uid}")
        except: pass
        kb=[[InlineKeyboardButton("💸 Оплатить TON", url=TON_LINK)],[InlineKeyboardButton("💬 Админ", url=f"https://t.me/{ADMIN_USERNAME}")],[InlineKeyboardButton("⬅️ Назад", callback_data="menu")]]
        await q.message.delete();await context.bot.send_message(uid, f"💳 Оплати:\n{TON_LINK}\nСкинь чек админу.", reply_markup=InlineKeyboardMarkup(kb));await q.answer()
    elif data=="admin":
        if not is_admin(uid): return await q.answer("Нет доступа", show_alert=True)
        kb=[[InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],[InlineKeyboardButton("⬅️ Назад", callback_data="menu")]]
        await q.message.delete();await context.bot.send_message(uid, "🔧 Админ-панель", reply_markup=InlineKeyboardMarkup(kb));await q.answer()
    elif data=="admin_stats":
        if not is_admin(uid): return
        cur.execute("SELECT COUNT(*) FROM users");users_count=cur.fetchone()[0]
        await q.answer(f"Юзеров: {users_count}", show_alert=True)
async def start(update, context): await show_main(update, context)
def main():
    app=ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    print("Bot running...");app.run_polling()
if __name__=="__main__": main()
