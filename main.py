
import os
import json
import time
import requests
from concurrent.futures import ThreadPoolExecutor

# --- CONFIGURATION ---
API_TOKEN = os.getenv('BOT_TOKEN', '8787470835:AAHO6sBhCqcpu9fLiVTQrIN4FMaugOcF7o0')
BASE_URL = f"https://api.telegram.org/bot{API_TOKEN}/"
OWNER_USERNAME = "Niro_X12"
PAYMENT_CHANNEL = "@Birr_lab_tech"
REFERRAL_BONUS = 2.0
MIN_WITHDRAW = 40.0

DEFAULT_CHANNELS = [
    "https://t.me/Crypto_Topup_F",
    "https://t.me/Mind_Boos",
    "https://t.me/ethio_free_channel2266",
    "https://t.me/onlinebussness127",
    "https://t.me/Birr_lab_tech",
    "https://t.me/alpha_bet_12"
]

DB_FILE = "bot_database.json"

session = requests.Session()
executor = ThreadPoolExecutor(max_workers=100)

def load_db():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {"users": {}, "channels": DEFAULT_CHANNELS, "phones": {}}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

db = load_db()

def send_api_request(method, payload):
    url = BASE_URL + method
    try:
        response = session.post(url, json=payload, timeout=5)
        return response.json()
    except Exception:
        return None

def send_message(chat_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    executor.submit(send_api_request, "sendMessage", payload)

def get_user(user_id):
    str_id = str(user_id)
    if str_id not in db["users"]:
        db["users"][str_id] = {
            "balance": 0.0,
            "referrals": 0,
            "referred_by": None,
            "banned": False,
            "phone": None,
            "wallet_name": None,
            "wallet_number": None,
            "step": None
        }
        save_db(db)
    return db["users"][str_id]

def get_contact_keyboard():
    return {
        "keyboard": [[{"text": "📱 ስልክ ቁጥርዎን ያጋሩ / Share Contact", "request_contact": True}]],
        "resize_keyboard": True,
        "one_time_keyboard": True
    }

def get_customer_menu():
    return {
        "keyboard": [
            [{"text": "💰 Balance"}, {"text": "👥 Invite Friends"}],
            [{"text": "💳 Wallet"}, {"text": "💸 Withdraw"}]
        ],
        "resize_keyboard": True
    }

def get_owner_menu():
    return {
        "keyboard": [
            [{"text": "💰 Balance"}, {"text": "👥 Invite Friends"}],
            [{"text": "💳 Wallet"}, {"text": "💸 Withdraw"}],
            [{"text": "🚫 Ban"}, {"text": "✅ Unban"}],
            [{"text": "➕ Add Channel"}, {"text": "➖ Remove Channel"}],
            [{"text": "📢 Broadcast"}]
        ],
        "resize_keyboard": True
    }

def get_channel_inline_markup():
    inline_keyboard = []
    channels = db["channels"]
    for i in range(0, len(channels), 2):
        row = [{"text": f"🔹 ቻናል #{i+1}", "url": channels[i]}]
        if i + 1 < len(channels):
            row.append({"text": f"🔹 ቻናል #{i+2}", "url": channels[i+1]})
        inline_keyboard.append(row)
    inline_keyboard.append([{"text": "🟢 Joined (ተቀላቅያለሁ)", "callback_data": "check_joined"}])
    return {"inline_keyboard": inline_keyboard}

def handle_updates(update):
    if "message" in update:
        msg = update["message"]
        chat_id = msg["chat"]["id"]
        user_id = str(msg["from"]["id"])
        username = msg["from"].get("username", "")
        text = msg.get("text", "")
        
        user = get_user(user_id)
        
        if user["banned"]:
            send_message(chat_id, "🔴 <b>ማስጠንቀቂያ፡</b> መልቲ-አካውንት (Multi-account) በመጠቀምዎ አካውንትዎ ታግዷል (Banned)!")
            return

        if "contact" in msg:
            phone = msg["contact"]["phone_number"]
            if phone in db["phones"] and db["phones"][phone] != user_id:
                user["banned"] = True
                save_db(db)
                send_message(chat_id, "🔴 <b>ማስጠንቀቂያ፡</b> በሌላ የቴሌግራም አካውንትዎ የገባችሁበት ስለሆነ አካውንትዎ ታግዷል (Banned)!")
                return
            
            db["phones"][phone] = user_id
            user["phone"] = phone
            
            if user["referred_by"] and user["referred_by"] in db["users"]:
                ref_id = user["referred_by"]
                db["users"][ref_id]["balance"] += REFERRAL_BONUS
                db["users"][ref_id]["referrals"] += 1
                send_message(ref_id, f"🟢 <b>አዲስ ጥቆማ!</b> በአንተ ሊንክ ሰው ገብቷል:: +{REFERRAL_BONUS} Birr ተጨምሯል!")
                user["referred_by"] = None

            save_db(db)
            send_message(chat_id, "🟢 <b>ስልክ ቁጥርዎ በስኬት ተረጋግጧል!</b>")
            send_join_channels(chat_id)
            return

        if text.startswith("/start"):
            user["step"] = None
            args = text.split()
            if len(args) > 1 and not user["referred_by"]:
                ref = args[1]
                if ref != user_id and ref in db["users"]:
                    user["referred_by"] = ref
                    save_db(db)

            if not user["phone"]:
                send_message(chat_id, "🔵 <b>እንኳን ወደ FAA Bot በደህና መጡ!</b>\n\n🟢 ቦቱን ለመጠቀም እባክዎን ስልክ ቁጥርዎን ያጋሩ።", get_contact_keyboard())
            else:
                send_join_channels(chat_id)
            return

        menu_buttons = ["💰 Balance", "👥 Invite Friends", "💳 Wallet", "💸 Withdraw", "🚫 Ban", "✅ Unban", "➕ Add Channel", "➖ Remove Channel", "📢 Broadcast"]
        if text in menu_buttons:
            user["step"] = None

        if username.lower() == OWNER_USERNAME.lower():
            if text == "🚫 Ban":
                user["step"] = "ban"
                save_db(db)
                send_message(chat_id, "🔵 <b>ለማገድ የሚፈልጉትን ID ያስገቡ:</b>")
                return
            elif text == "✅ Unban":
                user["step"] = "unban"
                save_db(db)
                send_message(chat_id, "🔵 <b>እግዱን ለማንሳት የሚፈልጉትን ID ያስገቡ:</b>")
                return
            elif text == "➕ Add Channel":
                user["step"] = "add_ch"
                save_db(db)
                send_message(chat_id, "🔵 <b>የሚጨመረውን ቻናል Link ያስገቡ:</b>")
                return
            elif text == "➖ Remove Channel":
                user["step"] = "rm_ch"
                save_db(db)
                send_message(chat_id, "🔵 <b>የሚሰረዘውን ቻናል Link ያስገቡ:</b>")
                return
            elif text == "📢 Broadcast":
                user["step"] = "broadcast"
                save_db(db)
                send_message(chat_id, "🔵 <b>የሚላከውን መልእክት ያስገቡ:</b>")
                return

        if text == "💰 Balance":
            send_message(chat_id, f"🟢 <b>የእርስዎ balance:</b> {user['balance']} Birr\n👥 <b>የጋበዟቸው ሰዎች:</b> {user['referrals']}")
            return
        elif text == "👥 Invite Friends":
            bot_info = send_api_request("getMe", {})
            bot_name = bot_info["result"]["username"] if bot_info else ""
            link = f"https://t.me/{bot_name}?start={user_id}"
            send_message(chat_id, f"🔵 <b>የእርስዎ የመጋበዣ ሊንክ፡</b>\n<code>{link}</code>\n\n🟢 <b>ለአንድ ሰው:</b> {REFERRAL_BONUS} Birr ያገኛሉ።")
            return
        elif text == "💳 Wallet":
            user["step"] = "wallet"
            save_db(db)
            send_message(chat_id, "🔵 <b>እባክዎን የTelebirr ስምና ቁጥርዎን ያስገቡ፡</b>\n<i>(ምሳሌ: Abebe Kebede 0912345678)</i>")
            return
        elif text == "💸 Withdraw":
            if not user["wallet_number"]:
                send_message(chat_id, "🔴 <b>ማስጠንቀቂያ፡</b> አስቀድመው 💳 Wallet ውስጥ ገብተው የTelebirr መረጃዎን ያስገቡ!")
                return
            if user["balance"] >= MIN_WITHDRAW:
                amt = user["balance"]
                user["balance"] = 0.0
                save_db(db)
                admin_text = (
                    f"📥 <b>አዲስ Withdraw Request!</b>\n\n"
                    f"👤 <b>User:</b> @{username} (ID: <code>{user_id}</code>)\n"
                    f"💰 <b>መጠን:</b> {amt} Birr\n"
                    f"👤 <b>ስም:</b> {user['wallet_name']}\n"
                    f"📱 <b>Telebirr:</b> <code>{user['wallet_number']}</code>"
                )
                send_message(PAYMENT_CHANNEL, admin_text)
                send_message(chat_id, f"🟢 <b>{amt} Birr Successful!</b> የብድር ጥያቄዎ ተልኳል::")
            else:
                send_message(chat_id, f"🔴 <b>ማስጠንቀቂያ፡</b> አነስተኛው የማውጫ መጠን {MIN_WITHDRAW} Birr ነው።")
            return

        step = user.get("step")
        if step == "wallet":
            parts = text.split()
            if len(parts) >= 2:
                user["wallet_name"] = " ".join(parts[:-1])
                user["wallet_number"] = parts[-1]
                user["step"] = None
                save_db(db)
                send_message(chat_id, "🟢 <b>የመክፈያ መረጃዎ በስኬት ተመዝግቧል (Successful)!</b>")
            else:
                send_message(chat_id, "🔴 <b>ስህተት!</b> እባክዎን ስም እና ስልክ ቁጥር ያስገቡ።")
            return
        elif step == "ban":
            target = text.replace("@", "").strip()
            for uid, udata in db["users"].items():
                if uid == target:
                    udata["banned"] = True
                    break
            save_db(db)
            user["step"] = None
            send_message(chat_id, f"🔴 <b>User {target} ታግዷል!</b>")
            return
        elif step == "unban":
            target = text.strip()
            if target in db["users"]:
                db["users"][target]["banned"] = False
                save_db(db)
            user["step"] = None
            send_message(chat_id, f"🟢 <b>User {target} እግዱ ተነስቷል!</b>")
            return
        elif step == "add_ch":
            if text not in db["channels"]:
                db["channels"].append(text.strip())
                save_db(db)
            user["step"] = None
            send_message(chat_id, "🟢 <b>ቻናሉ ተጨምሯል!</b>")
            return
        elif step == "rm_ch":
            if text in db["channels"]:
                db["channels"].remove(text.strip())
                save_db(db)
            user["step"] = None
            send_message(chat_id, "🟢 <b>ቻናሉ ተሰርዟል!</b>")
            return
        elif step == "broadcast":
            count = 0
            user["step"] = None
            save_db(db)
            send_message(chat_id, "🔄 <b>መልእክቱ እየተላከ ነው...</b>")
            for uid in list(db["users"].keys()):
                try:
                    send_message(uid, text)
                    count += 1
                except:
                    pass
            send_message(chat_id, f"🟢 <b>መልእክቱ ለ {count} ተጠቃሚዎች ተልኳል!</b>")
            return

    elif "callback_query" in update:
        cb = update["callback_query"]
        chat_id = cb["message"]["chat"]["id"]
        username = cb["from"].get("username", "")
        
        user = get_user(str(cb["from"]["id"]))
        if user["banned"]:
            send_message(chat_id, "🔴 <b>ማስጠንቀቂያ፡</b> መልቲ-አካውንት (Multi-account) በመጠቀምዎ አካውንትዎ ታግዷል (Banned)!")
            return

        if cb["data"] == "check_joined":
            if username.lower() == OWNER_USERNAME.lower():
                send_message(chat_id, "🟢 <b>እንኳን ደህና መጡ ባለቤቱ! Main Menu:</b>", get_owner_menu())
            else:
                send_message(chat_id, "🟢 <b>እንኳን ደህና መጡ! Main Menu:</b>", get_customer_menu())

def send_join_channels(chat_id):
    msg_text = "🔵 <b>FAA Bot</b>\n\n🔹 <b>እባክዎን ቦቱን ለመጠቀም ቀጣዮቹን ቻናሎች ይቀላቀሉ፡</b>"
    send_message(chat_id, msg_text, get_channel_inline_markup())

def main():
    print("FAA Bot is running 24/7 on Cloud...")
    offset = 0
    while True:
        try:
            updates = send_api_request("getUpdates", {"offset": offset, "timeout": 10})
            if updates and "result" in updates:
                for update in updates["result"]:
                    executor.submit(handle_updates, update)
                    offset = update["update_id"] + 1
        except Exception:
            pass
        time.sleep(0.01)

if __name__ == "__main__":
    main()
