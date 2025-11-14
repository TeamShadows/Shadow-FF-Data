# -*- coding: utf-8 -*-
"""
Professional Telegram Bot for Free Fire Emote Execution
Now includes:
- /emote
- /5g
- /6g
- /lag
- Fancy Replies
- Force-Join System
- Full Error Handling

Suitable for VPS deployment.
"""

import logging
import re
import json
import time
from typing import List, Optional

import requests
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ================== CONFIGURATION ==================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger("EmoteBot")

BOT_TOKEN = '8572170474:AAEZYuttRYzxMH3JLVySWq6hbKC5052mVGc'

# API BASES
EMOTE_ACTION_API_BASE = 'http://72.61.169.188:2004'
GROUP_ACTION_API_BASE = 'http://72.61.169.188:2009'
LAG_ACTION_API_BASE   = 'http://72.61.169.188:2010'
EMOTE_INFO_URL        = 'https://raw.githubusercontent.com/TeamShadows/Shadow-FF-Data/main/itemData.json'

REQUEST_TIMEOUT = 12
LONG_POLLING_TIMEOUT = 20
RETRY_DELAY = 5
CACHE_DURATION = 3600  # 1 hour

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/91.0.4472.124 Safari/537.36'
    )
}

# ============ FORCE-JOIN CONFIGURATION ============

REQUIRED_CHANNELS = [
    "@ShadowGamerzFF",
    "@ShadowGamerzOfficial"
]

CHANNEL_BUTTONS = [
    ("Shadow Gamerz FF", "https://t.me/ShadowGamerzFF"),
    ("Shadow Gamerz Official", "https://t.me/ShadowGamerzOfficial"),
]

# Global cache
items_cache: Optional[List[dict]] = None
cache_timestamp: float = 0


# ================== UTILITY FUNCTIONS ==================

def fancy_text(text: str) -> str:
    """Convert text to fancy small caps."""
    table = str.maketrans(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
        "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ"
    )
    return text.translate(table)


def format_text(text: str) -> str:
    """Apply fancy + bold markdown."""
    return f"*{fancy_text(text)}*"


def validate_bot_token(bot: TeleBot) -> bool:
    """Validate bot token by fetching bot info."""
    try:
        info = bot.get_me()
        logger.info(f"✅ Bot token valid. Logged in as: {info.username} (id={info.id})")
        return True
    except Exception as e:
        logger.error(f"❌ Invalid bot token or network error during validation: {e}")
        return False
# =============== FORCE JOIN HELPERS ===============

def check_force_join(user_id: int) -> List[str]:
    """Check if user joined required channels."""
    not_joined: List[str] = []
    for channel in REQUIRED_CHANNELS:
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status in ("left", "kicked"):
                not_joined.append(channel)
        except Exception:
            not_joined.append(channel)
    return not_joined


def send_force_join_message(chat_id: int) -> None:
    """Send force-join message with channel buttons."""
    markup = InlineKeyboardMarkup(row_width=1)
    for title, url in CHANNEL_BUTTONS:
        markup.add(InlineKeyboardButton(text=title, url=url))

    markup.add(InlineKeyboardButton("✅ Join Kar Liya, Check Karo", callback_data="check_join"))

    text = (
        "⚠️ *Bot use karne ke liye pehle ye channels join karo:*\n\n"
        "1️⃣ @ShadowGamerzFF\n"
        "2️⃣ @ShadowGamerzOfficial\n\n"
        "Join karne ke baad niche *✅ button* dabao."
    )

    bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)



# ================== DATA FETCHING ==================

def get_items_data() -> List[dict]:
    """Fetch & cache emote list."""
    global items_cache, cache_timestamp
    now = time.time()

    if items_cache is None or (now - cache_timestamp > CACHE_DURATION):
        try:
            logger.info("🔄 Fetching emote list JSON...")
            r = requests.get(EMOTE_INFO_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            items_cache = r.json()
            cache_timestamp = now
            logger.info(f"✅ Loaded {len(items_cache)} items.")
        except:
            logger.warning("⚠️ Failed to fetch emote list!")
            if items_cache is None:
                items_cache = []

    return items_cache or []


def get_emote_name(emote_id: int) -> str:
    for item in get_items_data():
        if str(item.get("Id")) == str(emote_id):
            return item.get("name", f"Emote {emote_id}")
    return f"Emote {emote_id}"



# ================== BOT INITIALIZATION ==================

bot = TeleBot(BOT_TOKEN)

if not validate_bot_token(bot):
    raise SystemExit("❌ Invalid Bot Token — Bot Stopped.")



# ========== START / HELP ==========

@bot.message_handler(commands=['start', 'help'])
def start_message(message):
    user_id = message.from_user.id

    not_joined = check_force_join(user_id)
    if not_joined:
        send_force_join_message(message.chat.id)
        return

    instructions = format_text("""
🔥 WELCOME TO THE EMOTE BOT 🔥

COMMANDS:
/emote <TEAMCODE> <UIDS> <EMOTEID>
/5g <UID>
/6g <UID>
/lag <TEAMCODE>

EXAMPLES:
/emote 7488876 1299021866 909000075
/5g 1299021866
/6g 1299021866
/lag 7488876

👉 Bot join karega, emote/lag/group karega, auto-leave karega.
    """)

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🌐 Browse Emotes", url="https://shadow-emote-list.vercel.app/"),
        InlineKeyboardButton("Support 🎉", url="https://t.me/ShadowGamerzFF")
    )
    markup.add(
        InlineKeyboardButton("Developer ⚡", url="https://t.me/theshadowowner"),
        InlineKeyboardButton("Main Channel", url="https://t.me/ShadowGamerzofficial")
    )

    bot.reply_to(message, instructions, parse_mode='Markdown', reply_markup=markup)



# ========== /emote COMMAND ==========

@bot.message_handler(commands=['emote'])
def handle_emote(message):
    try:
        user_id = message.from_user.id

        if check_force_join(user_id):
            send_force_join_message(message.chat.id)
            return

        args = message.text.split()[1:]
        if len(args) < 3:
            bot.reply_to(message, format_text("❌ USAGE: /emote TEAMCODE UID EMOTEID"))
            return

        team_code = args[0].strip()
        emote_id_str = args[-1].strip()
        uids = [u.strip() for u in args[1:-1]]

        if not re.match(r'^\d{7}$', team_code):
            bot.reply_to(message, format_text("❌ TEAM CODE 7 DIGIT KA HONA CHAHIYE"))
            return

        if not emote_id_str.isnumeric():
            bot.reply_to(message, format_text("❌ EMOTE ID NUMBER HONA CHAHIYE"))
            return

        emote_id = int(emote_id_str)

        if len(uids) == 0 or len(uids) > 4:
            bot.reply_to(message, format_text("❌ UIDs 1–4 ENTER KARO"))
            return

        uid_params = uids + [''] * (4 - len(uids))

        url = (
            f"{EMOTE_ACTION_API_BASE}/emote?"
            f"tc={team_code}&uid1={uid_params[0]}&uid2={uid_params[1]}"
            f"&uid3={uid_params[2]}&uid4={uid_params[3]}&emote_id={emote_id}"
        )

        r = requests.get(url, headers=HEADERS, timeout=LONG_POLLING_TIMEOUT)
        data = r.json()

        if data.get("status") != "success":
            bot.reply_to(message, format_text(f"❌ FAILED: {data.get('message')}"))
            return

        emote_name = get_emote_name(emote_id)

        msg = format_text(f"""
✅ EMOTE EXECUTED

TEAM: {team_code}
UIDS: {', '.join(uids)}
EMOTE: {emote_name}
ID: {emote_id}
        """)

        bot.reply_to(message, msg, parse_mode='Markdown')

    except Exception as e:
        logger.error(e)
        bot.reply_to(message, format_text("❌ ERROR — Try again"))
# ========== /5g COMMAND (5-PLAYER GROUP) ==========

@bot.message_handler(commands=['5g'])
def handle_5g(message):
    try:
        user_id = message.from_user.id
        if check_force_join(user_id):
            send_force_join_message(message.chat.id)
            return

        args = message.text.split()[1:]
        if len(args) != 1:
            bot.reply_to(message, format_text("❌ USE: /5g UID"))
            return

        uid = args[0].strip()
        if not uid.isnumeric():
            bot.reply_to(message, format_text("❌ UID NUMBER HONA CHAHIYE"))
            return

        url = f"{GROUP_ACTION_API_BASE}/5group?uid={uid}"
        r = requests.get(url, headers=HEADERS, timeout=LONG_POLLING_TIMEOUT)
        data = r.json()

        if data.get("status") != "success":
            bot.reply_to(message, format_text(f"❌ FAILED: {data.get('message')}"))
            return

        msg = format_text(f"""
✅ 5-PLAYER GROUP SENT

UID: {uid}
MESSAGE: {data.get('message')}
        """)

        bot.reply_to(message, msg, parse_mode='Markdown')

    except Exception as e:
        logger.error(e)
        bot.reply_to(message, format_text("❌ ERROR — Try Again"))



# ========== /6g COMMAND (6-PLAYER GROUP) ==========

@bot.message_handler(commands=['6g'])
def handle_6g(message):
    try:
        user_id = message.from_user.id
        if check_force_join(user_id):
            send_force_join_message(message.chat.id)
            return

        args = message.text.split()[1:]
        if len(args) != 1:
            bot.reply_to(message, format_text("❌ USE: /6g UID"))
            return

        uid = args[0].strip()
        if not uid.isnumeric():
            bot.reply_to(message, format_text("❌ UID NUMBER HONA CHAHIYE"))
            return

        url = f"{GROUP_ACTION_API_BASE}/6group?uid={uid}"
        r = requests.get(url, headers=HEADERS, timeout=LONG_POLLING_TIMEOUT)
        data = r.json()

        if data.get("status") != "success":
            bot.reply_to(message, format_text(f"❌ FAILED: {data.get('message')}"))
            return

        msg = format_text(f"""
✅ 6-PLAYER GROUP SENT

UID: {uid}
MESSAGE: {data.get('message')}
        """)

        bot.reply_to(message, msg, parse_mode='Markdown')

    except Exception as e:
        logger.error(e)
        bot.reply_to(message, format_text("❌ ERROR — Try Again"))



# ========== /lag COMMAND ==========

@bot.message_handler(commands=['lag'])
def handle_lag(message):
    try:
        user_id = message.from_user.id
        if check_force_join(user_id):
            send_force_join_message(message.chat.id)
            return

        args = message.text.split()[1:]
        if len(args) != 1:
            bot.reply_to(message, format_text("❌ USE: /lag TEAMCODE"))
            return

        tc = args[0].strip()
        if not re.match(r'^\d{7}$', tc):
            bot.reply_to(message, format_text("❌ TEAM CODE 7 DIGIT HONA CHAHIYE"))
            return

        url = f"{LAG_ACTION_API_BASE}/lag?tc={tc}"
        r = requests.get(url, headers=HEADERS, timeout=LONG_POLLING_TIMEOUT)
        data = r.json()

        if data.get("status") != "success":
            bot.reply_to(message, format_text(f"❌ FAILED: {data.get('message')}"))
            return

        msg = format_text(f"""
✅ LAG REQUEST SENT

TEAM CODE: {tc}
MESSAGE: {data.get('message')}
WAIT: {data.get('wait_seconds')}
        """)

        bot.reply_to(message, msg, parse_mode='Markdown')

    except Exception as e:
        logger.error(e)
        bot.reply_to(message, format_text("❌ ERROR — Try Again"))



# ========== CALLBACK HANDLER ==========

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    try:
        if call.data == "check_join":
            user_id = call.from_user.id

            if check_force_join(user_id):
                bot.answer_callback_query(call.id, "❌ Pehle channels join karo!", show_alert=True)
            else:
                bot.answer_callback_query(call.id, "✅ Verified!", show_alert=True)
                start_message(call.message)
            return

        bot.answer_callback_query(call.id)

    except Exception:
        pass



# ========== MAIN POLLING LOOP ==========

if __name__ == "__main__":
    logger.info("🤖 BOT STARTED!")
    logger.info("📡 Emote API: " + EMOTE_ACTION_API_BASE)

    while True:
        try:
            bot.infinity_polling(
                timeout=LONG_POLLING_TIMEOUT,
                long_polling_timeout=LONG_POLLING_TIMEOUT,
                skip_pending=True
            )
        except Exception as e:
            logger.error(f"❌ Polling crashed: {e}")
            time.sleep(RETRY_DELAY)
