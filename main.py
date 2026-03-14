import os
import asyncio
import logging
import re
from datetime import datetime
from pyrogram import Client, filters, idle
from telebot import TeleBot
from dotenv import load_dotenv

# Sozlamalarni yuklash
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- KONFIGURATSIYA ---
API_ID = int(os.getenv("API_ID", "30858730"))
API_HASH = os.getenv("API_HASH", "25106c9d80e8d8354053c1da9391edb8")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8769316813:AAGG_qt2faKYjXq8LxuiQhkBz56fsc6We3s")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7740552653"))
GROUP_ID = int(os.getenv("GROUP_ID", "-1001549017357"))
TARGET_BOT = "ochiqbudjet_5_bot" # Userbot kuzatadigan bot
UPDATE_INTERVAL = int(os.getenv("UPDATE_INTERVAL", "300"))
SESSION_DATA = os.getenv("STRING_SESSION", "AgHjAvAApBR1KFpVkWFYH3zWlkpd14Odc2nUeBd6gWRBix_fmqCiD-1BFyNbWWQu_bd38KvaG3wtXpBFTP2ulvpYWQaLj6xFRZbpuaNJKlE8Utevn6PjxS06HNRUGh43d15y5iH3O6YE-G95cBqvW4A7S3LFRDnS6Ofk4hfh0dj-GC43wD_hqcBxws1Y0OQ7AernvFlFtk-Opw5O-b8vl7RKrPWcrrlXrBg4U2gT6lTHRe3MREkbZdGveG7lhVdQqrrY25EjtmDn2t-qjLpvZwQ81K-IsjnfYc8obkGogwwwSBq6Q5QqMwoOh8tUPUIEN4UB_n6czgEhA6DP8mEcYqBi7r7hqgAAAAFTaP8IAA")

# Obyektlarni yaratish
user_bot = Client("my_userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_DATA, in_memory=True)
main_bot = TeleBot(BOT_TOKEN)

# Global xabar ID kesh
last_msg_id = None

# --- YORDAMCHI FUNKSIYALAR ---

async def click_inline_button(message, text_to_find):
    """Userbot orqali tugmalarni bosish"""
    if message.reply_markup:
        for row in message.reply_markup.inline_keyboard:
            for button in row:
                if text_to_find in button.text:
                    try:
                        await user_bot.request_callback_answer(message.chat.id, message.id, button.callback_data)
                        return True
                    except Exception as e:
                        logger.error(f"Tugma bosishda xato: {e}")
    return False

def parse_votes(text):
    """Reytingni matndan ajratish"""
    lines = text.split('\n')
    data = []
    for line in lines:
        match = re.search(r"(?:\*\*|)(\d+)(?:\*\*|)\s*(?:—|-|:)\s*(.+)", line)
        if match:
            votes = match.group(1)
            name = re.sub(r"[\*_`~]", "", match.group(2).strip())
            data.append({"votes": votes, "name": name})
    return data

# --- USERBOT LOGIKASI (KUZATUVCHI) ---

@user_bot.on_message(filters.chat(TARGET_BOT) & filters.bot)
async def monitor_target_bot(client, message):
    global last_msg_id
    
    # 1. Menyularni bosib o'tish
    if any(x in message.text for x in ["Viloyatni tanlang", "Hududni tanlang"]):
        await click_inline_button(message, "Namangan viloyati")
    elif any(x in message.text for x in ["Tumaningizni tanlang", "Tuman tanlang"]):
        await click_inline_button(message, "Chust tumani")
    
    # 2. Reyting ma'lumotini olish va ASOSIY BOT orqali yuborish
    elif "CHUST TUMANI" in message.text or "Ovoz" in message.text:
        ranking = parse_votes(message.text)
        if ranking:
            now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            report = f"📊 **CHUST TUMANI - JORIY REYTING**\n🕒 Yangilandi: `{now}`\n\n"
            for i, item in enumerate(ranking[:10], 1):
                report += f"{i}. **{item['votes']}** — {item['name']}\n"
            report += f"\n♻️ _Har {UPDATE_INTERVAL//60} daqiqada yangilanadi._"
            
            # --- ASOSIY BOT INTEGRATSIYASI ---
            try:
                # Guruhga yuborish (tahrirlash yoki yangi)
                if last_msg_id:
                    try:
                        main_bot.edit_message_text(report, GROUP_ID, last_msg_id, parse_mode="Markdown")
                    except Exception:
                        msg = main_bot.send_message(GROUP_ID, report, parse_mode="Markdown")
                        last_msg_id = msg.message_id
                else:
                    msg = main_bot.send_message(GROUP_ID, report, parse_mode="Markdown")
                    last_msg_id = msg.message_id
                
                # Adminga yuborish
                main_bot.send_message(ADMIN_ID, f"✅ Reyting yangilandi va guruhga yuborildi.\n\n{report}", parse_mode="Markdown")
                logger.info("Reyting muvaffaqiyatli integratsiya qilindi.")
            except Exception as e:
                logger.error(f"Asosiy bot xabar yuborishda xato: {e}")

async def auto_refresh():
    """Userbot har 5 daqiqada /start yuboradi"""
    while True:
        try:
            await user_bot.send_message(TARGET_BOT, "/start")
            logger.info("Userbot: Target botga so'rov yuborildi.")
        except Exception as e:
            logger.error(f"Refresh xatosi: {e}")
        await asyncio.sleep(UPDATE_INTERVAL)

async def start_services():
    """Barcha servislarni birga ishga tushirish"""
    try:
        await user_bot.start()
        logger.info("Userbot kuzatuvni boshladi!")
        
        # Avtomatik yangilashni fonda ishga tushirish
        asyncio.create_task(auto_refresh())
        
        # Userbotni to'xtab qolmasligi uchun idle holatda ushlash
        await idle()
    except Exception as e:
        logger.error(f"Tizimda xato: {e}")
    finally:
        await user_bot.stop()

if __name__ == "__main__":
    # Dasturni ishga tushirish
    asyncio.run(start_services())
