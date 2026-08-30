import sqlite3
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

TOKEN = "8978557088:AAEcUaIUydU9XfrBMBeFhHdo0J3KDu_OaOs"
bot = telebot.TeleBot(TOKEN)

OWNERS = [123456789]  # Replace with actual Telegram Numeric User IDs of @Niro_X12 and @Mezmur2003 if needed

# Database Setup
def init_db():
    conn = sqlite3.connect("bot_database.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance REAL DEFAULT 0.0,
            referred_by INTEGER,
            is_banned INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            channel_username TEXT PRIMARY KEY
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wallets (
            user_id INTEGER PRIMARY KEY,
            provider TEXT,
            account_info TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_db():
    return sqlite3.connect("bot_database.db", check_same_thread=False)

# Helper to check channels
def check_forced_sub(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT channel_username FROM channels")
    channels = cursor.fetchall()
    conn.close()

    for (ch,) in channels:
        try:
            member = bot.get_chat_member(ch, user_id)
            if member.status in ['left', 'kicked']:
                return False
        except Exception:
            pass
    return True

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"

    # Check ban
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT is_banned FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    if res and res[0] == 1:
        conn.close()
        bot.send_message(message.chat.id, "⚠️ አንተ ከቦቱ ታግደሃል! (You are banned from this bot.)")
        return

    # Register user if new
    if not res:
        args = message.text.split()
        ref_id = None
        if len(args) > 1 and args[1].isdigit():
            potential_ref = int(args[1])
            if potential_ref != user_id:
                ref_id = potential_ref
                cursor.execute("UPDATE users SET balance = balance + 2.0 WHERE user_id = ?", (ref_id,))
        
        cursor.execute("INSERT OR IGNORE INTO users (user_id, username, referred_by) VALUES (?, ?, ?)", (user_id, username, ref_id))
        conn.commit()
    conn.close()

    # Check subscriptions
    if not check_forced_sub(user_id):
        markup = InlineKeyboardMarkup()
        default_channels = [
            ("Crypto Topup", "https://t.me/Crypto_Topup_F"),
            ("Make Money Bot", "https://t.me/makemoneyb_bot"),
            ("Biruk Channel", "https://t.me/with_biruk0"),
            ("Money Hustler", "https://t.me/money_hustlerr")
        ]
        for name, url in default_channels:
            markup.add(InlineKeyboardButton(text=name, url=url))
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT channel_username FROM channels")
        db_chs = cursor.fetchall()
        conn.close()
        for (ch,) in db_chs:
            markup.add(InlineKeyboardButton(text=ch, url=f"https://t.me/{ch.replace('@', '')}"))

        markup.row(
            InlineKeyboardButton(text="📢 Channel", url="https://t.me/Crypto_Topup_F"),
            InlineKeyboardButton(text="💳 Payment Proof", url="https://t.me/makemoneyproof")
        )
        markup.row(
            InlineKeyboardButton(text="🔗 Sponsor", url="https://t.me/with_biruk0"),
            InlineKeyboardButton(text="🔗 Sponsor", url="https://t.me/money_hustlerr")
        )

        markup.add(InlineKeyboardButton(text="✅ Joined", callback_data="check_join"))
        
        bot.send_message(
            message.chat.id,
            "⚠️ **ሁሉም ቻናሎች ማطናል አለብዎት**\n\nእስከአሁን ያሉትን ቻናሎች join ካደረጉ በኋላ ከታች ያለውን '✅ Joined' የሚለውን ይጫኑ።",
            parse_mode="Markdown",
            reply_markup=markup
        )
        return

    show_main_menu(message.chat.id, user_id)

def show_main_menu(chat_id, user_id):
    markup = InlineKeyboardMarkup()
    if user_id in OWNERS:
        markup.row(
            InlineKeyboardButton(text="👥 Invite Friends", callback_data="invite"),
            InlineKeyboardButton(text="💰 Balance", callback_data="balance")
        )
        markup.row(
            InlineKeyboardButton(text="🚫 Ban", callback_data="ban_user"),
            InlineKeyboardButton(text="✅ Unban", callback_data="unban_user")
        )
        markup.row(
            InlineKeyboardButton(text="➕ Add Channel", callback_data="add_channel"),
            InlineKeyboardButton(text="❌ Remove Channel", callback_data="remove_channel")
        )
        markup.row(
            InlineKeyboardButton(text="📢 Broadcast", callback_data="broadcast"),
            InlineKeyboardButton(text="👛 Wallet", callback_data="wallet")
        )
    else:
        markup.row(
            InlineKeyboardButton(text="💰 Balance", callback_data="balance"),
            InlineKeyboardButton(text="👥 Invite Friends", callback_data="invite")
        )
        markup.row(
            InlineKeyboardButton(text="👛 Wallet", callback_data="wallet"),
            InlineKeyboardButton(text="📤 Withdraw", callback_data="withdraw")
        )

    bot.send_message(chat_id, "👋 እንኳን ደህና መጡ! ከታች ካሉት አማራጮች አንዱን ይምረጡ:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    data = call.data

    if data == "check_join":
        if check_forced_sub(user_id):
            bot.answer_callback_query(call.id, "✅ ተሳክቷል!")
            bot.delete_message(call.message.chat.id, call.message.message_id)
            show_main_menu(call.message.chat.id, user_id)
        else:
            bot.answer_callback_query(call.id, "❌ ሁሉንም ቻናሎች ገና አልjoin አደረጉም!", show_alert=True)

    elif data == "balance":
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        res = cursor.fetchone()
        conn.close()
        bal = res[0] if res else 0.0
        bot.answer_callback_query(call.id, f"የእርስዎ አካውንት ሚዛን: {bal} ብር", show_alert=True)

    elif data == "invite":
        bot_info = bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
        bot.send_message(call.message.chat.id, f"👥 **የእርስዎ የጋበዣ ሊንክ (Referral Link):**\n\n{ref_link}\n\n1 ሰው ሲጋብዙ 2 ብር ያገኛሉ!", parse_mode="Markdown")

    elif data == "wallet":
        msg = bot.send_message(call.message.chat.id, "لطفاً የቴሌብር ስምዎን እና ቁጥርዎን ይጻፉ (Enter Telebirr Name and Number):")
        bot.register_next_step_handler(msg, save_wallet_step)

    elif data == "withdraw":
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        res = cursor.fetchone()
        cursor.execute("SELECT account_info FROM wallets WHERE user_id = ?", (user_id,))
        wallet_res = cursor.fetchone()
        conn.close()

        bal = res[0] if res else 0.0
        if not wallet_res:
            bot.answer_callback_query(call.id, "⚠️ እባክዎ በመጀመሪያ wallet በመንካት የቴሌብር መረጃዎን ያስገቡ!", show_alert=True)
            return

        if bal >= 40:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET balance = balance - 40 WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()

            bot.send_message(call.message.chat.id, "✅ Successful! የገንዘብ ማውጣት ጥያቄዎ ተሳክቷል አሁን ወደ @makemoneyproof ተልኳል።")
            bot.send_message("@makemoneyproof", f"📤 **New Withdraw Request**\nUser: {call.from_user.first_name}\nID: {user_id}\nWallet: {wallet_res[0]}\nAmount: 40 Birr", parse_mode="Markdown")
        else:
            bot.answer_callback_query(call.id, f"⚠️ የገንዘብዎ መጠን 40 ብር መሞላት አለበት። የአሁን balans: {bal} Birr", show_alert=True)

    elif data == "ban_user" and user_id in OWNERS:
        msg = bot.send_message(call.message.chat.id, "እባክዎ ሊያግዱት የሚፈልጉትን የሰውን User ID ወይም Username ያስገቡ:")
        bot.register_next_step_handler(msg, process_ban)

    elif data == "unban_user" and user_id in OWNERS:
        msg = bot.send_message(call.message.chat.id, "እባክዎ ከባን ሊያወጡት የሚፈልጉትን User ID ያስገቡ:")
        bot.register_next_step_handler(msg, process_unban)

    elif data == "add_channel" and user_id in OWNERS:
        msg = bot.send_message(call.message.chat.id, "እባክዎ ሊጨምሩት የሚፈልጉትን ቻናል Username ያስገቡ (ለምሳሌ: @channel):")
        bot.register_next_step_handler(msg, process_add_channel)

    elif data == "remove_channel" and user_id in OWNERS:
        msg = bot.send_message(call.message.chat.id, "እባክዎ ሊያስወግዱት የሚፈልጉትን ቻናል Username ያስገቡ:")
        bot.register_next_step_handler(msg, process_remove_channel)

    elif data == "broadcast" and user_id in OWNERS:
        msg = bot.send_message(call.message.chat.id, "ለህዝብ ማስተላለፍ የሚፈልጉትን መልእክት ይላኩ:")
        bot.register_next_step_handler(msg, process_broadcast)

def save_wallet_step(message):
    user_id = message.from_user.id
    info = message.text
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO wallets (user_id, provider, account_info) VALUES (?, ?, ?)", (user_id, "Telebirr", info))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ Successful! የቴሌብር መረጃዎ ተመዝግቧል።")

def process_ban(message):
    target = message.text.strip()
    conn = get_db()
    cursor = conn.cursor()
    if target.isdigit():
        cursor.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (int(target),))
    else:
        cursor.execute("UPDATE users SET is_banned = 1 WHERE username = ?", (target.replace('@', ''),))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ ተጠቃሚው ታግዷል (User Banned Successfully).")

def process_unban(message):
    target = message.text.strip()
    conn = get_db()
    cursor = conn.cursor()
    if target.isdigit():
        cursor.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (int(target),))
    else:
        cursor.execute("UPDATE users SET is_banned = 0 WHERE username = ?", (target.replace('@', ''),))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ ተጠቃሚው ከባን ወጥቷል (User Unbanned).")

def process_add_channel(message):
    ch = message.text.strip()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO channels (channel_username) VALUES (?)", (ch,))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f"✅ {ch} ቻናሉ ተጨምሯል።")

def process_remove_channel(message):
    ch = message.text.strip()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM channels WHERE channel_username = ?", (ch,))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f"✅ {ch} ቻናሉ ተወግዷል።")

def process_broadcast(message):
    text = message.text
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()

    success = 0
    for (uid,) in users:
        try:
            bot.send_message(uid, f"📢 **Announcement**\n\n{text}", parse_mode="Markdown")
            success += 1
        except Exception:
            pass
    bot.send_message(message.chat.id, f"✅ Broadcast sent successfully to {success} users.")

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()

