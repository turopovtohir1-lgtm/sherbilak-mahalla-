import os
import asyncio
import logging
import re
from datetime import datetime
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
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

# --- SOZLAMALAR (Railway/GitHub ENV lardan olinadi) ---
API_ID = int(os.getenv("API_ID", "30858730"))
API_HASH = os.getenv("API_HASH", "25106c9d80e8d8354053c1da9391edb8")
STRING_SESSION = os.getenv("STRING_SESSION") # Railway uchun juda muhim!
BOT_TOKEN = os.getenv("BOT_TOKEN", "8769316813:AAGG_qt2faKYjXq8LxuiQhkBz56fsc6We3s")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7740552653"))
GROUP_ID = int(os.getenv("GROUP_ID", "-1001549017357"))
TARGET_BOT = "@ochiqbudjet_5_bot"
UPDATE_INTERVAL = int(os.getenv("UPDATE_INTERVAL", "300"))

# Userbot (Pyrogram) - String Session orqali
if STRING_SESSION:
    app = Client("my_userbot", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)
else:
    # Mahalliy sinov uchun oddiy session
    app = Client("my_userbot", api_id=API_ID, api_hash=API_HASH)

# Asosiy Bot (TeleBot) - Guruhga xabar yuborish uchun
main_bot = TeleBot(BOT_TOKEN)

# Global o'zgaruvchi
last_msg_id = None

async def click_inline_button(message, text_to_find):
    """Inline tugmani matni bo'yicha bosish"""
    if message.reply_markup:
        for row in message.reply_markup.inline_keyboard:
            for button in row:
                if text_to_find in button.text:
                    logger.info(f"Tugma bosilmoqda: {button.text}")
                    try:
                        await app.request_callback_answer(message.chat.id, message.id, button.callback_data)
                        return True
                    except Exception as e:
                        logger.error(f"Callback xatosi: {e}")
    return False

def parse_votes(text):
    """Botdan kelgan matndan ovozlarni tahlil qilish"""
    # Bu qismni @ochiqbudjet_5_bot beradigan real matnga moslash kerak
    # Misol: 1. **125** — Tashabbus nomi
    lines = text.split('\n')
    data = []
    for line in lines:
        match = re.search(r"\*\*(\d+)\*\*\s*—\s*(.+)", line)
        if match:
            data.append({"votes": match.group(1), "name": match.group(2).strip()})
    return data

@app.on_message(filters.chat(TARGET_BOT) & filters.bot)
async def handle_target_bot(client, message):
    global last_msg_id
    logger.info(f"Target botdan xabar: {message.text[:50]}...")

    # 1. Viloyat tanlash (Namangan)
    if "Viloyatni tanlang" in message.text or "Hududni tanlang" in message.text:
        await click_inline_button(message, "Namangan viloyati")
    
    # 2. Tuman tanlash (Chust)
    elif "Tumaningizni tanlang" in message.text or "Tuman tanlang" in message.text:
        await click_inline_button(message, "Chust tumani")
    
    # 3. Reytingni olish
    elif "CHUST TUMANI" in message.text or "Ovoz" in message.text:
        ranking = parse_votes(message.text)
        if ranking:
            now = datetime.now().strftime("%H:%M:%S")
            report = f"📊 **CHUST TUMANI - TOP 10 REYTING**\n🕒 Yangilandi: `{now}`\n\n"
            for i, item in enumerate(ranking[:10], 1):
                report += f"{i}. **{item['votes']}** — {item['name']}\n"
            report += f"\n♻️ _Har {UPDATE_INTERVAL//60} daqiqada yangilanadi._"
            
            try:
                if last_msg_id:
                    main_bot.edit_message_text(report, GROUP_ID, last_msg_id, parse_mode="Markdown")
                else:
                    msg = main_bot.send_message(GROUP_ID, report, parse_mode="Markdown")
                    last_msg_id = msg.message_id
                logger.info("Reyting guruhda yangilandi.")
            except Exception as e:
                if "message is not modified" not in str(e):
                    msg = main_bot.send_message(GROUP_ID, report, parse_mode="Markdown")
                    last_msg_id = msg.message_id

async def auto_refresh():
    """Har 5 daqiqada /start yuborib turish"""
    while True:
        try:
            await app.send_message(TARGET_BOT, "/start")
            logger.info("Monitoring yangilanmoqda...")
        except Exception as e:
            logger.error(f"Refresh xatosi: {e}")
        await asyncio.sleep(UPDATE_INTERVAL)

async def main():
    await app.start()
    logger.info("Userbot ishga tushdi!")
    # Avtomatik yangilashni boshlash
    asyncio.create_task(auto_refresh())
    await idle()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
