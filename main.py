import os
import asyncio
import logging
import re
import threading
from datetime import datetime, timezone, timedelta
from pyrogram import Client, filters, idle
from pyrogram.errors import (
    FloodWait, MessageNotModified, MessageIdInvalid,
    ChatWriteForbidden, UserDeactivated, AuthKeyUnregistered
)
from telebot import TeleBot
from telebot.apihelper import ApiTelegramException
from dotenv import load_dotenv

# ─── SOZLAMALAR ────────────────────────────────────────────────────────────────
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("SherbilakBot")

# O'zbekiston vaqt mintaqasi (UTC+5)
UZT = timezone(timedelta(hours=5))

def uztime() -> str:
    return datetime.now(UZT).strftime("%H:%M:%S")

def uzdatetime() -> str:
    return datetime.now(UZT).strftime("%d.%m.%Y %H:%M:%S")

# ─── KONFIGURATSIYA ─────────────────────────────────────────────────────────────
API_ID        = int(os.getenv("API_ID", "30858730"))
API_HASH      = os.getenv("API_HASH", "25106c9d80e8d8354053c1da9391edb8")
BOT_TOKEN     = os.getenv("BOT_TOKEN", "8769316813:AAGG_qt2faKYjXq8LxuiQhkBz56fsc6We3s")
ADMIN_ID      = int(os.getenv("ADMIN_ID", "7740552653"))
GROUP_ID      = int(os.getenv("GROUP_ID", "-1001549017357"))
TARGET_BOT    = os.getenv("TARGET_BOT", "ochiqbudjet_5_bot")
UPDATE_INTERVAL = 120          # 2 daqiqa (sekund)
STRING_SESSION = "AgHjAvAApBR1KFpVkWFYH3zWlkpd14Odc2nUeBd6gWRBix_fmqCiD-1BFyNbWWQu_bd38KvaG3wtXpBFTP2ulvpYWQaLj6xFRZbpuaNJKlE8Utevn6PjxS06HNRUGh43d15y5iH3O6YE-G95cBqvW4A7S3LFRDnS6Ofk4hfh0dj-GC43wD_hqcBxws1Y0OQ7AernvFlFtk-Opw5O-b8vl7RKrPWcrrlXrBg4U2gT6lTHRe3MREkbZdGveG7lhVdQqrrY25EjtmDn2t-qjLpvZwQ81K-IsjnfYc8obkGogwwwSBq6Q5QqMwoOh8tUPUIEN4UB_n6czgEhA6DP8mEcYqBi7r7hqgAAAAFTaP8IAA"

# ─── GLOBAL HOLAT ───────────────────────────────────────────────────────────────
# Guruhga yuborilgan oxirgi xabar ID sini saqlaydi
last_msg_id: int | None = None
# Event loop — asyncio ↔ threading ko'prigi uchun
_loop: asyncio.AbstractEventLoop | None = None
# Monitoring faol yoki yo'q
monitoring_active = False

# ─── BOTLAR ─────────────────────────────────────────────────────────────────────
app = Client(
    name="my_userbot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=STRING_SESSION,
    in_memory=True
)

main_bot = TeleBot(BOT_TOKEN, threaded=False)

# ─── YORDAMCHI: ADMINGA XABAR ───────────────────────────────────────────────────
def notify_admin(text: str):
    """Adminga xabar yuboradi. Barcha xatoliklarni log qiladi."""
    try:
        main_bot.send_message(ADMIN_ID, text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Admin xabari yuborilmadi: {e}")

# ─── GURUHGA XABAR YUBORISH / TAHRIRLASH ────────────────────────────────────────
def send_or_edit_report(text: str):
    """
    Mantiq:
    1. last_msg_id mavjud → tahrirlashga urinish
    2. Tahrirda MessageIdInvalid (o'chirilgan) → yangisini yuborish
    3. MessageNotModified → xech narsa qilma (matn o'zgarmagan)
    4. Guruhda yangi xabar paydo bo'lganidan keyin (edit imkonsiz) → yangisini yuborish
    """
    global last_msg_id

    def _send_new():
        global last_msg_id
        msg = main_bot.send_message(GROUP_ID, text, parse_mode="Markdown")
        last_msg_id = msg.message_id
        logger.info(f"Yangi xabar yuborildi. ID: {last_msg_id}")

    if last_msg_id:
        try:
            main_bot.edit_message_text(text, GROUP_ID, last_msg_id, parse_mode="Markdown")
            logger.info(f"Xabar tahrirlandi. ID: {last_msg_id}")
        except ApiTelegramException as e:
            err = str(e).lower()
            if "message is not modified" in err:
                # Matn o'zgarmagan — normal holat
                logger.debug("Xabar o'zgarmagan, tahrirlash o'tkazib yuborildi.")
            elif "message to edit not found" in err or "message_id_invalid" in err:
                # Xabar o'chirilgan — yangisini yubor
                logger.warning("Eski xabar topilmadi, yangi yuboriladi.")
                _send_new()
            elif "chat not found" in err:
                logger.error("Guruh topilmadi! GROUP_ID ni tekshiring.")
                notify_admin("❌ *Xato:* Guruh topilmadi. `GROUP_ID` ni tekshiring!")
            else:
                # Boshqa xato (flood va h.k.) — yangi xabar yuborib ko'r
                logger.warning(f"Tahrirda noma'lum xato: {e}. Yangi xabar yuboriladi.")
                try:
                    _send_new()
                except Exception as e2:
                    logger.error(f"Yangi xabar ham yuborilmadi: {e2}")
                    notify_admin(f"❌ *Xabar yuborishda xato:*\n`{e2}`")
        except Exception as e:
            logger.error(f"Kutilmagan xato (edit): {e}")
            notify_admin(f"❌ *Kutilmagan xato:*\n`{e}`")
    else:
        try:
            _send_new()
        except Exception as e:
            logger.error(f"Birinchi xabar yuborilmadi: {e}")
            notify_admin(f"❌ *Birinchi xabar yuborishda xato:*\n`{e}`")

# ─── ASOSIY BOT HANDLERLARI ──────────────────────────────────────────────────────
@main_bot.message_handler(commands=['start'])
def handle_start(message):
    uid = message.from_user.id
    if uid != ADMIN_ID:
        main_bot.send_message(uid, "⛔ Ruxsat yo'q.")
        return

    status = "✅ Faol" if monitoring_active else "⏸ Kutish"
    main_bot.send_message(
        ADMIN_ID,
        f"👋 *Sherbilak OpenBudjet Monitoring*\n\n"
        f"📡 Holat: {status}\n"
        f"🕒 Vaqt: `{uzdatetime()}`\n"
        f"🔄 Yangilanish: har *{UPDATE_INTERVAL // 60} daqiqa*\n\n"
        f"Buyruqlar:\n"
        f"/start — holat\n"
        f"/refresh — qo'lda yangilash\n"
        f"/status — batafsil holat",
        parse_mode="Markdown"
    )
    logger.info("Admin /start bosdi.")

@main_bot.message_handler(commands=['refresh'])
def handle_refresh(message):
    if message.from_user.id != ADMIN_ID:
        return
    main_bot.send_message(ADMIN_ID, "🔄 Qo'lda yangilash boshlandi...")
    # Asyncio event loopiga vazifa qo'shish (thread-safe)
    if _loop and _loop.is_running():
        asyncio.run_coroutine_threadsafe(_manual_refresh(), _loop)
    else:
        main_bot.send_message(ADMIN_ID, "⚠️ Userbot hali ishga tushmagan.")

@main_bot.message_handler(commands=['status'])
def handle_status(message):
    if message.from_user.id != ADMIN_ID:
        return
    status_text = (
        f"📊 *Tizim holati*\n\n"
        f"🤖 Userbot: {'✅ Faol' if app.is_connected else '❌ Uzilgan'}\n"
        f"📡 Monitoring: {'✅ Faol' if monitoring_active else '⏸ Kutish'}\n"
        f"📨 Oxirgi xabar ID: `{last_msg_id or 'Yuq'}`\n"
        f"🕒 Hozirgi vaqt (UZT): `{uzdatetime()}`\n"
        f"🔄 Yangilanish oraliq: `{UPDATE_INTERVAL}s`"
    )
    main_bot.send_message(ADMIN_ID, status_text, parse_mode="Markdown")

# ─── USERBOT: INLINE TUGMA BOSISH ───────────────────────────────────────────────
async def click_btn(message, btn_text: str) -> bool:
    """Inline klaviatura tugmasini topib bosadi."""
    if not message.reply_markup:
        return False
    for row in message.reply_markup.inline_keyboard:
        for btn in row:
            if btn_text.lower() in (btn.text or "").lower():
                try:
                    await app.request_callback_answer(
                        chat_id=message.chat.id,
                        message_id=message.id,
                        callback_data=btn.callback_data,
                        timeout=15
                    )
                    logger.info(f"Tugma bosildi: '{btn.text}'")
                    return True
                except FloodWait as fw:
                    logger.warning(f"FloodWait: {fw.value}s kutilmoqda.")
                    await asyncio.sleep(fw.value)
                    return False
                except Exception as e:
                    logger.error(f"Tugma bosishda xato ('{btn_text}'): {e}")
                    return False
    logger.warning(f"Tugma topilmadi: '{btn_text}'")
    return False

# ─── USERBOT: XABARLARNI KUZATISH ───────────────────────────────────────────────
@app.on_message(filters.private)
async def monitor(client, message):
    """ochiqbudjet botidan kelgan xabarlarni qayta ishlaydi."""
    global monitoring_active

    # Faqat target bot xabarlarini qayta ishla
    if not message.from_user:
        return
    if message.from_user.username != TARGET_BOT:
        return

    text = message.text or message.caption or ""
    if not text:
        return

    logger.info(f"Target botdan xabar: {text[:80]}...")
    monitoring_active = True

    # ── Viloyat tanlash ──
    if any(x in text for x in ["Viloyatni tanlang", "Hududni tanlang", "viloyat"]):
        await asyncio.sleep(1)
        clicked = await click_btn(message, "Namangan")
        if not clicked:
            notify_admin("⚠️ 'Namangan viloyati' tugmasi topilmadi!")

    # ── Tuman tanlash ──
    elif any(x in text for x in ["Tumaningizni tanlang", "Tuman tanlang", "tuman"]):
        await asyncio.sleep(1)
        clicked = await click_btn(message, "Chust")
        if not clicked:
            notify_admin("⚠️ 'Chust tumani' tugmasi topilmadi!")

    # ── Reyting natijasi ──
    elif "CHUST" in text.upper() or any(x in text for x in ["Ovoz", "ovoz", "reyting", "Reyting", "#"]):
        lines = text.split('\n')
        res = []

        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Formatlar: "1. Ism — 100", "1 — Ism: 200", "#1 Ism 300"
            match = re.search(
                r"(?:#?\s*)?(\d+)[\.\)\s]*[-—:]\s*(.+?)[\s—:]+(\d+)\s*(?:ovoz|ta)?$",
                line, re.IGNORECASE
            )
            if match:
                num   = match.group(1)
                name  = re.sub(r'[*_`~]', '', match.group(2).strip())
                votes = match.group(3)
                medal = {"1": "🥇", "2": "🥈", "3": "🥉"}.get(num, f"*{num}.*")
                res.append(f"{medal} {name} — *{votes}* ovoz")
            else:
                # Raqam bor bo'lsa ham olish
                match2 = re.search(r"(\d+)\s*[-—:]\s*(.+)", line)
                if match2:
                    name = re.sub(r'[*_`~]', '', match2.group(2).strip())
                    res.append(f"▫️ *{match2.group(1)}* — {name}")

        if res:
            report = (
                f"📊 *CHUST TUMANI REYTINGI*\n"
                f"🕒 Yangilangan: `{uztime()}` \\(UZT\\)\n"
                f"━━━━━━━━━━━━━━━\n"
                + "\n".join(res[:15])
                + f"\n━━━━━━━━━━━━━━━\n"
                f"_Har {UPDATE_INTERVAL // 60} daqiqada yangilanadi_"
            )
            # Thread-safe guruhga yuborish
            if _loop and _loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    asyncio.to_thread(send_or_edit_report, report), _loop
                )
            notify_admin(
                f"✅ *Reyting yangilandi*\n"
                f"🕒 `{uzdatetime()}`\n"
                f"📌 Natijalar: {len(res)} ta"
            )
        else:
            logger.warning("Reyting ma'lumoti topilmadi (regex mos kelmadi).")
            logger.debug(f"Xabar matni:\n{text}")

# ─── AVTOMATIK YANGILASH ─────────────────────────────────────────────────────────
async def _manual_refresh():
    """Qo'lda yoki avtomatik yangilash."""
    try:
        await app.send_message(TARGET_BOT, "/start")
        logger.info("Refresh yuborildi → /start")
        notify_admin(f"🔄 Yangilash yuborildi: `{uzdatetime()}`")
    except FloodWait as fw:
        logger.warning(f"FloodWait: {fw.value}s")
        notify_admin(f"⏳ FloodWait: {fw.value} sekund kutish kerak.")
    except (UserDeactivated, AuthKeyUnregistered) as e:
        logger.critical(f"Sessiya muammosi: {e}")
        notify_admin(f"🔴 *Sessiya xatosi!* Qayta login kerak.\n`{e}`")
    except Exception as e:
        logger.error(f"Refresh xatosi: {e}")
        notify_admin(f"❌ *Refresh xatosi:*\n`{e}`")

async def auto_refresher():
    """Har UPDATE_INTERVAL sekundda avtomatik yangilaydi."""
    await asyncio.sleep(5)  # Ishga tushganda biroz kutish
    while True:
        await _manual_refresh()
        await asyncio.sleep(UPDATE_INTERVAL)

# ─── ASOSIY BOSHLASH ─────────────────────────────────────────────────────────────
def run_telebot():
    """TeleBot ni alohida threadda ishga tushiradi."""
    logger.info("TeleBot polling boshladi...")
    while True:
        try:
            main_bot.polling(none_stop=True, interval=1, timeout=30)
        except Exception as e:
            logger.error(f"TeleBot polling xatosi: {e}")
            notify_admin(f"⚠️ *TeleBot polling xatosi:*\n`{e}`\n_Qayta ulanmoqda..._")
            import time; time.sleep(5)

async def run_all():
    global _loop
    _loop = asyncio.get_running_loop()

    # TeleBot ni alohida threadda ishga tushur
    t = threading.Thread(target=run_telebot, daemon=True)
    t.start()
    logger.info("TeleBot thread ishga tushdi.")

    # Userbotni ishga tushur
    try:
        await app.start()
        me = await app.get_me()
        logger.info(f"Userbot ishga tushdi: @{me.username}")
        notify_admin(
            f"🟢 *Tizim ishga tushdi!*\n"
            f"👤 Userbot: `@{me.username}`\n"
            f"🕒 Vaqt: `{uzdatetime()}`\n"
            f"🔄 Yangilanish: har *{UPDATE_INTERVAL // 60} daqiqa*\n\n"
            f"Monitoring boshlandi ✅"
        )
    except (UserDeactivated, AuthKeyUnregistered) as e:
        logger.critical(f"Userbot ulanmadi: {e}")
        notify_admin(f"🔴 *Userbot ulanmadi!*\n`{e}`")
        return
    except Exception as e:
        logger.critical(f"Userbot ishga tushishda xato: {e}")
        notify_admin(f"🔴 *Userbot xatosi:*\n`{e}`")
        return

    # Avtomatik yangilovchini ishga tushur
    asyncio.create_task(auto_refresher())

    # Botni ishlayotgan holatda ushlab turadi
    await idle()

    # To'xtatilganda
    await app.stop()
    notify_admin("🔴 *Tizim to'xtatildi.*")

if __name__ == "__main__":
    asyncio.run(run_all())
