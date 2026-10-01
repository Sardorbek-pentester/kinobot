
# import asyncio
# import logging
# import re
# import sqlite3

# from aiogram import Bot, Dispatcher, F
# from aiogram.enums import ChatMemberStatus
# from aiogram.filters import Command, CommandStart
# from aiogram.types import (
#     CallbackQuery,
#     InlineKeyboardButton,
#     InlineKeyboardMarkup,
#     Message,
# )

# # ================== SOZLAMALAR ==================
# BOT_TOKEN = "8522521719:AAFIsBYRCp7xTFp89bnOlLrFGjzB7LZHrhU"
# ADMIN_IDS = {6962129622}       # sizning Telegram ID raqamingiz
# MAJBURIY_KANALLAR = ["@Sardorbek_Ulashov"]         # masalan: ["@kanalingiz"]  (bo'sh bo'lsa obuna tekshirilmaydi)
# # =================================================

# logging.basicConfig(level=logging.INFO)
# log = logging.getLogger("bot")

# # Izohdan kodni topish: "#12", "Kod: 12", "kod 12"
# KOD_REGEX = re.compile(r"#(\d+)|(?:kod|code)\s*[:\-]?\s*(\d+)", re.IGNORECASE)

# db = sqlite3.connect("darslar.db")
# db.execute("""CREATE TABLE IF NOT EXISTS darslar(
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     kod TEXT NOT NULL,
#     turi TEXT NOT NULL,
#     file_id TEXT NOT NULL,
#     izoh TEXT,
#     manba TEXT UNIQUE
# )""")
# db.execute("CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY)")
# db.commit()

# bot = Bot(BOT_TOKEN)
# dp = Dispatcher()

# YUBORUVCHILAR = {
#     "video": bot.send_video,
#     "document": bot.send_document,
#     "photo": bot.send_photo,
#     "audio": bot.send_audio,
#     "animation": bot.send_animation,
#     "voice": bot.send_voice,
# }


# # ================== YORDAMCHI FUNKSIYALAR ==================
# def kodni_top(matn):
#     if not matn:
#         return None
#     m = KOD_REGEX.search(matn)
#     return (m.group(1) or m.group(2)) if m else None


# def faylni_ol(msg: Message):
#     """Xabardagi fayl turi va file_id sini qaytaradi."""
#     if msg.video:
#         return "video", msg.video.file_id
#     if msg.document:
#         return "document", msg.document.file_id
#     if msg.photo:
#         return "photo", msg.photo[-1].file_id
#     if msg.audio:
#         return "audio", msg.audio.file_id
#     if msg.animation:
#         return "animation", msg.animation.file_id
#     if msg.voice:
#         return "voice", msg.voice.file_id
#     return None, None


# def darsni_saqla(msg: Message, manba: str):
#     """Xabarni bazaga saqlaydi. Kod topilsa kodni, bo'lmasa None qaytaradi."""
#     turi, file_id = faylni_ol(msg)
#     kod = kodni_top(msg.caption)
#     if not turi or not kod:
#         return None
#     db.execute(
#         "INSERT OR REPLACE INTO darslar(kod, turi, file_id, izoh, manba) "
#         "VALUES (?, ?, ?, ?, ?)",
#         (kod, turi, file_id, msg.caption, manba),
#     )
#     db.commit()
#     return kod


# def darslar(kod):
#     return db.execute(
#         "SELECT turi, file_id, izoh FROM darslar WHERE kod = ? ORDER BY id", (kod,)
#     ).fetchall()


# def user_qosh(uid):
#     db.execute("INSERT OR IGNORE INTO users(user_id) VALUES (?)", (uid,))
#     db.commit()


# async def obuna_bolmagan(uid):
#     yoq = []
#     for ch in MAJBURIY_KANALLAR:
#         try:
#             a = await bot.get_chat_member(ch, uid)
#             if a.status in (ChatMemberStatus.LEFT, ChatMemberStatus.KICKED):
#                 yoq.append(ch)
#         except Exception as e:
#             # Bot kanalda admin bo'lmasa tekshira olmaydi — foydalanuvchini to'smaymiz
#             log.warning("%s tekshirilmadi (bot u yerda adminmi?): %s", ch, e)
#     return yoq


# def obuna_tugmalari(kanallar, kod):
#     rows = [
#         [InlineKeyboardButton(text=f"➕ {ch}", url=f"https://t.me/{ch.lstrip('@')}")]
#         for ch in kanallar
#     ]
#     rows.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data=f"t:{kod}")])
#     return InlineKeyboardMarkup(inline_keyboard=rows)


# async def dars_yubor(chat_id, kod):
#     for turi, file_id, izoh in darslar(kod):
#         try:
#             await YUBORUVCHILAR[turi](
#                 chat_id,
#                 file_id,
#                 caption=izoh,
#                 protect_content=True,  # uzatish va saqlash yopiq
#             )
#         except Exception as e:
#             log.error("Kod %s yuborilmadi: %s", kod, e)
#             await bot.send_message(chat_id, "⚠️ Xatolik yuz berdi, keyinroq urinib ko'ring.")


# # ================== KANAL POSTLARI (avtomatik saqlash) ==================
# @dp.channel_post()
# async def kanal_posti(msg: Message):
#     kod = darsni_saqla(msg, f"{msg.chat.id}:{msg.message_id}")
#     if kod:
#         log.info("Kanaldan saqlandi: kod %s (%s)", kod, msg.chat.title)


# @dp.edited_channel_post()
# async def kanal_tahrir(msg: Message):
#     kod = darsni_saqla(msg, f"{msg.chat.id}:{msg.message_id}")
#     if kod:
#         log.info("Tahrirdan saqlandi: kod %s", kod)


# # ================== FOYDALANUVCHI ==================
# @dp.message(CommandStart())
# async def start(msg: Message):
#     user_qosh(msg.from_user.id)
#     await msg.answer(
#         "Assalomu alaykum! 👋\n\n"
#         "Videoda ko'rsatilgan dars kodini yuboring.\nMasalan: 12"
#     )


# @dp.callback_query(F.data.startswith("t:"))
# async def tekshir(call: CallbackQuery):
#     kod = call.data[2:]
#     if await obuna_bolmagan(call.from_user.id):
#         await call.answer("❗ Hali barcha kanallarga obuna bo'lmadingiz", show_alert=True)
#         return
#     await call.answer()
#     await call.message.delete()
#     await dars_yubor(call.from_user.id, kod)


# # ================== ADMIN ==================
# @dp.message(Command("help"), F.from_user.id.in_(ADMIN_IDS))
# async def yordam(msg: Message):
#     await msg.answer(
#         "👨‍💼 Admin buyruqlari:\n\n"
#         "📥 Dars qo'shish — kanaldagi darsni botga FORWARD qiling "
#         "(izohida #12 bo'lishi kerak)\n"
#         "📚 /list — barcha darslar\n"
#         "🗑 /del 12 — kodni o'chirish\n"
#         "📊 /stats — statistika\n"
#         "📢 /send — xabarga reply qilib yozing, hammaga yuboriladi"
#     )


# @dp.message(
#     F.from_user.id.in_(ADMIN_IDS),
#     F.video | F.document | F.photo | F.audio | F.animation | F.voice,
# )
# async def admin_fayl(msg: Message):
#     """Admin darsni forward qiladi yoki o'zi yuboradi — izohdagi kod bilan saqlanadi."""
#     origin = getattr(msg, "forward_origin", None)
#     if origin is not None and getattr(origin, "chat", None) and getattr(origin, "message_id", None):
#         manba = f"{origin.chat.id}:{origin.message_id}"   # kanaldan forward
#     else:
#         manba = f"admin:{msg.chat.id}:{msg.message_id}"
#     kod = darsni_saqla(msg, manba)
#     if kod:
#         await msg.answer(f"✅ Saqlandi! Kod: {kod}\nTekshirish uchun botga {kod} deb yozing.")
#     else:
#         await msg.answer("❗ Izohda kod topilmadi. Izohga #12 kabi kod yozing.")


# @dp.message(Command("list"), F.from_user.id.in_(ADMIN_IDS))
# async def royxat(msg: Message):
#     rows = db.execute(
#         "SELECT kod, COUNT(*), MIN(izoh) FROM darslar GROUP BY kod "
#         "ORDER BY CAST(kod AS INTEGER)"
#     ).fetchall()
#     if not rows:
#         await msg.answer("Hali dars yo'q.")
#         return
#     qatorlar = []
#     for kod, soni, izoh in rows:
#         nomi = (izoh or "").replace("\n", " ")[:40]
#         qatorlar.append(f"{kod} — {nomi} ({soni} ta fayl)")
#     await msg.answer(("📚 Darslar:\n\n" + "\n".join(qatorlar))[:4000])


# @dp.message(Command("del"), F.from_user.id.in_(ADMIN_IDS))
# async def ochir(msg: Message):
#     p = msg.text.split()
#     if len(p) < 2:
#         await msg.answer("Format: /del 12")
#         return
#     kod = p[1].lstrip("#")
#     cur = db.execute("DELETE FROM darslar WHERE kod = ?", (kod,))
#     db.commit()
#     await msg.answer(f"🗑 Kod {kod} o'chirildi" if cur.rowcount else "Bunday kod yo'q")


# @dp.message(Command("stats"), F.from_user.id.in_(ADMIN_IDS))
# async def stats(msg: Message):
#     u = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
#     d = db.execute("SELECT COUNT(DISTINCT kod) FROM darslar").fetchone()[0]
#     await msg.answer(f"📊 Statistika\n\n👥 Foydalanuvchilar: {u}\n📚 Darslar: {d}")


# @dp.message(Command("send"), F.from_user.id.in_(ADMIN_IDS))
# async def tarqat(msg: Message):
#     if not msg.reply_to_message:
#         await msg.answer("Tarqatiladigan xabarga reply qilib /send yozing.")
#         return
#     ids = [r[0] for r in db.execute("SELECT user_id FROM users").fetchall()]
#     await msg.answer(f"⏳ {len(ids)} ta foydalanuvchiga yuborilmoqda...")
#     ok = 0
#     for uid in ids:
#         try:
#             await msg.reply_to_message.copy_to(uid)
#             ok += 1
#         except Exception:
#             pass
#         await asyncio.sleep(0.05)
#     await msg.answer(f"✅ Yuborildi: {ok} / {len(ids)}")


# # ================== KOD QABUL QILISH (eng oxirida) ==================
# @dp.message(F.text)
# async def kod_qabul(msg: Message):
#     user_qosh(msg.from_user.id)
#     kod = msg.text.strip().lstrip("#")
#     if not kod.isdigit():
#         await msg.answer("Iltimos, faqat dars kodini yuboring. Masalan: 12")
#         return
#     if not darslar(kod):
#         await msg.answer("❌ Bunday kod topilmadi. Tekshirib qayta yuboring.")
#         return
#     yoq = await obuna_bolmagan(msg.from_user.id)
#     if yoq:
#         await msg.answer(
#             "Darsni olish uchun kanalga obuna bo'ling va ✅ Tekshirish ni bosing:",
#             reply_markup=obuna_tugmalari(yoq, kod),
#         )
#         return
#     await dars_yubor(msg.chat.id, kod)


# async def main():
#     log.info("Bot ishga tushdi")
#     await dp.start_polling(bot)


# if __name__ == "__main__":
#     asyncio.run(main())

import asyncio
import logging
import re
import sqlite3

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ChatMemberStatus
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

# ================== SOZLAMALAR ==================
BOT_TOKEN = "8522521719:AAGLzivKAB3WlhyiZFSnBz513HvRQkRcvQ0"
ADMIN_IDS = {6962129622}                    # sizning Telegram ID raqamingiz
MAJBURIY_KANALLAR = ["@Sardorbek_Ulashov"]  # bo'sh [] bo'lsa obuna tekshirilmaydi
# =================================================

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("bot")

KOD_REGEX = re.compile(r"#(\d+)|(?:kod|code)\s*[:\-]?\s*(\d+)", re.IGNORECASE)

db = sqlite3.connect("darslar.db")
db.execute("""CREATE TABLE IF NOT EXISTS darslar(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kod TEXT NOT NULL,
    turi TEXT NOT NULL,
    file_id TEXT NOT NULL,
    izoh TEXT,
    manba TEXT UNIQUE
)""")
db.execute("CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY)")
db.commit()

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

YUBORUVCHILAR = {
    "video": bot.send_video,
    "document": bot.send_document,
    "photo": bot.send_photo,
    "audio": bot.send_audio,
    "animation": bot.send_animation,
    "voice": bot.send_voice,
}


# ================== YORDAMCHI FUNKSIYALAR ==================
def kodni_top(matn):
    if not matn:
        return None
    m = KOD_REGEX.search(matn)
    return (m.group(1) or m.group(2)) if m else None


def faylni_ol(msg: Message):
    if msg.video:
        return "video", msg.video.file_id
    if msg.document:
        return "document", msg.document.file_id
    if msg.photo:
        return "photo", msg.photo[-1].file_id
    if msg.audio:
        return "audio", msg.audio.file_id
    if msg.animation:
        return "animation", msg.animation.file_id
    if msg.voice:
        return "voice", msg.voice.file_id
    return None, None


def darsni_saqla(msg: Message, manba: str):
    turi, file_id = faylni_ol(msg)
    kod = kodni_top(msg.caption)
    if not turi or not kod:
        return None
    db.execute(
        "INSERT OR REPLACE INTO darslar(kod, turi, file_id, izoh, manba) "
        "VALUES (?, ?, ?, ?, ?)",
        (kod, turi, file_id, msg.caption, manba),
    )
    db.commit()
    return kod


def darslar(kod):
    return db.execute(
        "SELECT turi, file_id, izoh FROM darslar WHERE kod = ? ORDER BY id", (kod,)
    ).fetchall()


def user_qosh(uid):
    db.execute("INSERT OR IGNORE INTO users(user_id) VALUES (?)", (uid,))
    db.commit()


async def adminlarga_xabar(matn):
    for admin in ADMIN_IDS:
        try:
            await bot.send_message(admin, matn)
        except Exception:
            pass


async def obuna_bolmagan(uid):
    yoq = []
    for ch in MAJBURIY_KANALLAR:
        try:
            a = await bot.get_chat_member(ch, uid)
            log.info("Obuna tekshiruvi: user=%s kanal=%s holat=%s", uid, ch, a.status)
            if a.status in (ChatMemberStatus.LEFT, ChatMemberStatus.KICKED):
                yoq.append(ch)
        except Exception as e:
            log.warning("%s tekshirilmadi: %s", ch, e)
            await adminlarga_xabar(
                f"⚠️ {ch} kanalida obunani tekshirib bo'lmadi:\n{e}\n\n"
                "Bot shu kanalda ADMIN ekanini tekshiring. /obuna buyrug'ini yozing."
            )
    return yoq


def obuna_tugmalari(kanallar, kod):
    rows = [
        [InlineKeyboardButton(text=f"➕ {ch}", url=f"https://t.me/{ch.lstrip('@')}")]
        for ch in kanallar
    ]
    rows.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data=f"t:{kod}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def dars_yubor(chat_id, kod):
    for turi, file_id, izoh in darslar(kod):
        try:
            await YUBORUVCHILAR[turi](
                chat_id,
                file_id,
                caption=izoh,
                protect_content=True,
            )
        except Exception as e:
            log.error("Kod %s yuborilmadi: %s", kod, e)
            await bot.send_message(chat_id, "⚠️ Xatolik yuz berdi, keyinroq urinib ko'ring.")


# ================== KANAL POSTLARI (avtomatik saqlash) ==================
@dp.channel_post()
async def kanal_posti(msg: Message):
    kod = darsni_saqla(msg, f"{msg.chat.id}:{msg.message_id}")
    if kod:
        log.info("Kanaldan saqlandi: kod %s (%s)", kod, msg.chat.title)


@dp.edited_channel_post()
async def kanal_tahrir(msg: Message):
    kod = darsni_saqla(msg, f"{msg.chat.id}:{msg.message_id}")
    if kod:
        log.info("Tahrirdan saqlandi: kod %s", kod)


# ================== FOYDALANUVCHI ==================
@dp.message(CommandStart())
async def start(msg: Message):
    user_qosh(msg.from_user.id)
    await msg.answer(
        "Assalomu alaykum! 👋\n\n"
        "Videoda ko'rsatilgan dars kodini yuboring.\nMasalan: 12"
    )


@dp.callback_query(F.data.startswith("t:"))
async def tekshir(call: CallbackQuery):
    kod = call.data[2:]
    if await obuna_bolmagan(call.from_user.id):
        await call.answer("❗ Hali barcha kanallarga obuna bo'lmadingiz", show_alert=True)
        return
    await call.answer()
    await call.message.delete()
    await dars_yubor(call.from_user.id, kod)


# ================== ADMIN ==================
@dp.message(Command("help"), F.from_user.id.in_(ADMIN_IDS))
async def yordam(msg: Message):
    await msg.answer(
        "👨‍💼 Admin buyruqlari:\n\n"
        "📥 Dars qo'shish — kanaldagi darsni botga FORWARD qiling "
        "(izohida #12 bo'lishi kerak)\n"
        "📚 /list — barcha darslar\n"
        "🗑 /del 12 — kodni o'chirish\n"
        "📊 /stats — statistika\n"
        "🔎 /obuna — majburiy obuna sozlamasini tekshirish\n"
        "📢 /send — xabarga reply qilib yozing, hammaga yuboriladi"
    )


@dp.message(Command("obuna"), F.from_user.id.in_(ADMIN_IDS))
async def obuna_test(msg: Message):
    if not MAJBURIY_KANALLAR:
        await msg.answer("❗ MAJBURIY_KANALLAR ro'yxati bo'sh — obuna tekshirilmaydi.")
        return
    for ch in MAJBURIY_KANALLAR:
        try:
            chat = await bot.get_chat(ch)
            bot_holati = await bot.get_chat_member(ch, bot.id)
            sizning = await bot.get_chat_member(ch, msg.from_user.id)
            await msg.answer(
                f"🔎 {ch}\n"
                f"Nomi: {chat.title or chat.full_name}\n"
                f"Turi: {chat.type}\n"
                f"Bot holati: {bot_holati.status}\n"
                f"Sizning holatingiz: {sizning.status}"
            )
        except Exception as e:
            await msg.answer(f"❌ {ch} tekshirib bo'lmadi:\n{e}")


@dp.message(
    F.from_user.id.in_(ADMIN_IDS),
    F.video | F.document | F.photo | F.audio | F.animation | F.voice,
)
async def admin_fayl(msg: Message):
    origin = getattr(msg, "forward_origin", None)
    if origin is not None and getattr(origin, "chat", None) and getattr(origin, "message_id", None):
        manba = f"{origin.chat.id}:{origin.message_id}"
    else:
        manba = f"admin:{msg.chat.id}:{msg.message_id}"
    kod = darsni_saqla(msg, manba)
    if kod:
        await msg.answer(f"✅ Saqlandi! Kod: {kod}\nTekshirish uchun botga {kod} deb yozing.")
    else:
        await msg.answer("❗ Izohda kod topilmadi. Izohga #12 kabi kod yozing.")


@dp.message(Command("list"), F.from_user.id.in_(ADMIN_IDS))
async def royxat(msg: Message):
    rows = db.execute(
        "SELECT kod, COUNT(*), MIN(izoh) FROM darslar GROUP BY kod "
        "ORDER BY CAST(kod AS INTEGER)"
    ).fetchall()
    if not rows:
        await msg.answer("Hali dars yo'q.")
        return
    qatorlar = []
    for kod, soni, izoh in rows:
        nomi = (izoh or "").replace("\n", " ")[:40]
        qatorlar.append(f"{kod} — {nomi} ({soni} ta fayl)")
    await msg.answer(("📚 Darslar:\n\n" + "\n".join(qatorlar))[:4000])


@dp.message(Command("del"), F.from_user.id.in_(ADMIN_IDS))
async def ochir(msg: Message):
    p = msg.text.split()
    if len(p) < 2:
        await msg.answer("Format: /del 12")
        return
    kod = p[1].lstrip("#")
    cur = db.execute("DELETE FROM darslar WHERE kod = ?", (kod,))
    db.commit()
    await msg.answer(f"🗑 Kod {kod} o'chirildi" if cur.rowcount else "Bunday kod yo'q")


@dp.message(Command("stats"), F.from_user.id.in_(ADMIN_IDS))
async def stats(msg: Message):
    u = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    d = db.execute("SELECT COUNT(DISTINCT kod) FROM darslar").fetchone()[0]
    await msg.answer(f"📊 Statistika\n\n👥 Foydalanuvchilar: {u}\n📚 Darslar: {d}")


@dp.message(Command("send"), F.from_user.id.in_(ADMIN_IDS))
async def tarqat(msg: Message):
    if not msg.reply_to_message:
        await msg.answer("Tarqatiladigan xabarga reply qilib /send yozing.")
        return
    ids = [r[0] for r in db.execute("SELECT user_id FROM users").fetchall()]
    await msg.answer(f"⏳ {len(ids)} ta foydalanuvchiga yuborilmoqda...")
    ok = 0
    for uid in ids:
        try:
            await msg.reply_to_message.copy_to(uid)
            ok += 1
        except Exception:
            pass
        await asyncio.sleep(0.05)
    await msg.answer(f"✅ Yuborildi: {ok} / {len(ids)}")


# ================== KOD QABUL QILISH (eng oxirida) ==================
@dp.message(F.text)
async def kod_qabul(msg: Message):
    user_qosh(msg.from_user.id)
    kod = msg.text.strip().lstrip("#")
    if not kod.isdigit():
        await msg.answer("Iltimos, faqat dars kodini yuboring. Masalan: 12")
        return
    if not darslar(kod):
        await msg.answer("❌ Bunday kod topilmadi. Tekshirib qayta yuboring.")
        return
    yoq = await obuna_bolmagan(msg.from_user.id)
    if yoq:
        await msg.answer(
            "Darsni olish uchun kanalga obuna bo'ling va ✅ Tekshirish ni bosing:",
            reply_markup=obuna_tugmalari(yoq, kod),
        )
        return
    await dars_yubor(msg.chat.id, kod)


async def main():
    log.info("Bot ishga tushdi")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())