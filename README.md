# Open Budget Userbot Monitoring (Railway & GitHub Edition)

Ushbu loyiha **@ochiqbudjet_5_bot** orqali Namangan viloyati, Chust tumani tashabbuslar reytingini avtomatik ravishda skanerlab, Telegram guruhga yuborib turadi. **Railway** va **GitHub** uchun to'liq moslangan.

## 🚀 O'rnatish bosqichlari (Juda muhim!)

### 1-bosqich: String Session olish
Railway kabi platformalar har safar botni qayta ishga tushirganda telefon raqamingizni va SMS kodni so'ramaydi. Buning uchun `STRING_SESSION` kerak bo'ladi.
1. Mahalliy kompyuteringizda `pip install pyrogram tgcrypto` o'rnating.
2. `generate_session.py` faylini ishga tushiring: `python generate_session.py`.
3. Telefon raqamingizni va SMS kodni kiriting.
4. Olingan uzun kodni (String Session) nusxalab oling.

### 2-bosqich: GitHub va Railway ga yuklash
1. Ushbu fayllarni yangi GitHub repo-ga yuklang.
2. [Railway.app](https://railway.app) ga kiring va GitHub reponi bog'lang.
3. Railway **Variables** (Environment Variables) qismiga quyidagilarni qo'shing:
   - `API_ID`: `30858730`
   - `API_HASH`: `25106c9d80e8d8354053c1da9391edb8`
   - `BOT_TOKEN`: `8769316813:AAGG_qt2faKYjXq8LxuiQhkBz56fsc6We3s`
   - `ADMIN_ID`: `7740552653`
   - `GROUP_ID`: `-1001549017357`
   - `STRING_SESSION`: (1-bosqichda olingan uzun kod)
   - `UPDATE_INTERVAL`: `300` (5 daqiqa)

### 3-bosqich: Ishga tushirish
Railway avtomatik ravishda `Procfile` ni ko'radi va botni ishga tushiradi.

## 🛠 Tuzatilgan xatolar va yangiliklar:
*   **String Session:** Railway-da bot o'chib yonganda qayta login so'ramasligi ta'minlandi.
*   **Auto-Refresh:** Har 5 daqiqada botga `/start` yuborish orqali modalni yangilab turadi.
*   **Parsing:** Botdan keladigan matnni tahlil qilish logikasi yaxshilandi.
*   **Deployment:** GitHub va Railway uchun barcha kerakli fayllar (`Procfile`, `requirements.txt`) qo'shildi.

## ⚠️ Muhim eslatma:
Userbot sifatida o'z shaxsiy raqamingizni emas, balki boshqa (ishchi) raqamni ishlatish tavsiya etiladi. Telegram userbotlarni bloklashi mumkin bo'lgan holatlar mavjud, shuning uchun `UPDATE_INTERVAL` ni juda kichik qilib qo'ymang (minimal 300 tavsiya etiladi).
