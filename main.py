import os
import asyncio
import logging
import re
from datetime import datetime
from pyrogram import Client, filters, idle
from telebot import TeleBot
from dotenv import load_dotenv

# .env faylidan sozlamalarni yuklash
load_dotenv()

# Logging sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- SOZLAMALAR ---
# Barcha ID ma'lumotlari siz taqdim etganingizdek 100% aniq olingan
API_ID = int(os.getenv("API_ID", "30858730"))
API_HASH = os.getenv("API_HASH", "25106c9d80e8d8354053c1da9391edb8")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8769316813:AAGG_qt2faKYjXq8LxuiQhkBz56fsc6We3s")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7740552653"))
GROUP_ID = int(os.getenv("GROUP_ID", "-1001549017357"))
TARGET_BOT = "ochiqbudjet_5_bot" # Userbot kuzatadigan bot
UPDATE_INTERVAL = int(os.getenv("UPDATE_INTERVAL", "300"))
STRING_SESSION = os.getenv("STRING_SESSION", "AgHjAvAApBR1KFpVkWFYH3zWlkpd14Odc2nUeBd6gWRBix_fmqCiD-1BFyNbWWQu_bd38KvaG3wtXpBFTP2ulvpYWQaLj6xFRZbpuaNJKlE8Utevn6PjxS06HNRUGh43d15y5iH3O6YE-G95cBqvW4A7S3LFRDnS6Ofk4hfh0dj-GC43wD_hqcBxws1Y0OQ7AernvFlFtk-Opw5O-b8vl7RKrPWcrrlXrBg4U2gT6lTHRe3MREkbZdGveG7lhVdQqrrY25EjtmDn2t-qjLpvZwQ81K-IsjnfYc8obkGogwwwSBq6Q5QqMwoOh8tUPUIEN4UB_n6czgEhA6DP8mEcYqBi7r7hqgAAAAFTaP8IAA")

# Obyektlarni yaratish
# Userbot (Pyrogram) va Bot (TeleBot) integratsiyasi
app = Client(
    "my_userbot", 
    api_id=API_ID, 
    api_hash=API_HASH, 
    session_string=STRING_SESSION, 
    in_memory=True
)
main_bot = TeleBot(BOT_TOKEN)

# Global kesh
last_msg_id = None

# --- ASOSIY BOT (TeleBot) FUNKSIYALARI ---
# Admin /start bosganda javob bermaslik xatosi shu yerda tuzatildi
@main_bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.from_user.id == ADMIN_ID:
        main_bot.reply_to(message, "✅ Monitoring tizimi ishga tushgan. Men guruhga reytingni yuborib turaman.")
        logger.info("Admin botni start qildi.")
    else:
        main_bot.reply_to(message, "Siz admin emassiz.")

def send_to_group_and_admin(report):
    """Xabarni guruhga va adminga yuborish funksiyasi"""
    global last_msg_id
    try:
        # Guruhga yuborish yoki tahrirlash
        if last_msg_id:
            try:
                main_bot.edit_message_text(report, GROUP_ID, last_msg_id, parse_mode="Markdown")
            except Exception:
                msg = main_bot.send_message(GROUP_ID, report, parse_mode="Markdown")
                last_msg_id = msg.message_id
        else:
            msg = main_bot.send_message(GROUP_ID, report, parse_mode="Markdown")
            last_msg_id = msg.message_id
        
        # Adminga hisobot
        main_bot.send_message(ADMIN_ID, f"🔄 Reyting yangilandi:\n\n{report}", parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Xabar yuborishda xatolik: {e}")

# --- USERBOT (Pyrogram) FUNKSIYALARI ---

async def click_inline_button(message, text_to_find):
    """Inline tugmalarni avtomatik bosish"""
    if message.reply_markup:
        for row in message.reply_markup.inline_keyboard:
            for button in row:
                if text_to_find in button.text:
                    try:
                        await app.request_callback_answer(message.chat.id, message.id, button.callback_data)
                        return True
                    except Exception as e:
                        logger.error(f"Tugma bosishda xato: {e}")
    return False

def parse_votes(text):
    """Matndan reyting ma'lumotlarini ajratib olish"""
    lines = text.split('\n')
    data = []
    for line in lines:
        match = re.search(r"(?:\*\*|)(\d+)(?:\*\*|)\s*(?:—|-|:)\s*(.+)", line)
        if match:
            votes = match.group(1)
            name = re.sub(r"[\*_`~]", "", match.group(2).strip())
            data.append({"votes": votes, "name": name})
    return data

@app.on_message(filters.chat(TARGET_BOT) & filters.bot)
async def monitor_logic(client, message):
    """Target botdan kelgan xabarlarni tahlil qilish"""
    # Hududiy tanlovlar
    if any(x in message.text for x in ["Viloyatni tanlang", "Hududni tanlang"]):
        await click_inline_button(message, "Namangan viloyati")
    elif any(x in message.text for x in ["Tumaningizni tanlang", "Tuman tanlang"]):
        await click_inline_button(message, "Chust tumani")
    
    # Reytingni aniqlash
    elif "CHUST TUMANI" in message.text or "Ovoz" in message.text:
        ranking = parse_votes(message.text)
        if ranking:
            now = datetime.now().strftime("%H:%M:%S")
            report = f"📊 **CHUST TUMANI - TOP 10 REYTING**\n🕒 Yangilandi: `{now}`\n\n"
            for i, item in enumerate(ranking[:10], 1):
                report += f"{i}. **{item['votes']}** — {item['name']}\n"
            report += f"\n♻️ _Har {UPDATE_INTERVAL//60} daqiqada yangilanadi._"
            
            # Integratsiya: Userbot ma'lumotni TeleBot orqali yuboradi
            send_to_group_and_admin(report)

async def auto_refresh():
    """Doimiy monitoring so'rovi"""
    while True:
        try:
            await app.send_message(TARGET_BOT, "/start")
            logger.info("Monitoring so'rovi yuborildi.")
        except Exception as e:
            logger.error(f"Refresh xatosi: {e}")
        await asyncio.sleep(UPDATE_INTERVAL)

async def run_bot_polling():
    """TeleBot xabarlarni tinglashi uchun polling"""
    while True:
        try:
            main_bot.polling(none_stop=True, interval=1, timeout=20)
        except Exception as e:
            logger.error(f"TeleBot Polling xatosi: {e}")
            await asyncio.sleep(5)

async def main():
    try:
        # 1. Userbotni ishga tushirish
        await app.start()
        logger.info("Userbot ishga tushdi!")
        
        # 2. TeleBot Pollingni alohida taskda ishga tushirish (Admin /start bosganda javob berishi uchun)
        asyncio.create_task(asyncio.to_thread(main_bot.polling, none_stop=True))
        
        # 3. Avtomatik yangilashni boshlash
        asyncio.create_task(auto_refresh())
        
        await idle()
    except Exception as e:
        logger.error(f"Tizimda xato: {e}")
    finally:
        await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
