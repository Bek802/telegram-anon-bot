import os
import logging
from typing import Dict, Optional
from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
)

# --------------------------------------------------------------------------------
# LOGIKA UCHUN MUHIM ESLATMA:
# Anonim xabarlarga javob berish (Reply) funksiyasi ishlashi uchun
# bot yuborgan xabar ID'sini original jo'natuvchi ID'siga bog'lash kerak.
# Global lug'at (ANON_REPLY_MAP) faqat DEMONSTRATSIYA uchun ishlatiladi.
# RENDER/CLOUD muhitida DOIMIY ma'lumotlar bazasi (masalan, FIREBASE FIRESTORE) kerak!
# --------------------------------------------------------------------------------

# Anonim xabar yuborilganda, qabul qiluvchidagi xabar ID'sini original jo'natuvchi ID'siga bog'laydi.
# Format: {qabul_qiluvchi_xabar_id: original_jo'natuvchi_id}
ANON_REPLY_MAP: Dict[int, int] = {} 

# Logging sozlamalari
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Sizning TOKENingiz
TOKEN = os.environ.get("TOKEN", "8349538809:AAH99J3Wa0tR3WmEDqTrlXmEy-NpSDoA0MQ")

# /start komandasi (Chuqur havolani qabul qiladi)
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Chuqur havolani ('/start <target_id>') qabul qiladi yoki foydalanuvchining havolasini beradi.
    """
    if not update.message:
        return

    user_id = update.message.from_user.id
    bot_username = context.bot.username
    
    if context.args:
        # Chuqur havolani boshqarish: /start <target_id>
        try:
            target_id = int(context.args[0])
            
            if target_id == user_id:
                await update.message.reply_text("Siz o'zingizga anonim xabar yubora olmaysiz.")
                return
            
            # Maqsadli ID'ni suhbat kontekstida saqlash
            context.user_data['sending_to'] = target_id
            
            await update.message.reply_text(
                f"✍️ Siz endi **{target_id} ID'li foydalanuvchiga** anonim xabar yuborishga tayyorsiz.\n"
                "Iltimos, xabaringizni yuboring (matn, rasm, stiker...).",
                parse_mode='Markdown'
            )
            logger.info(f"User {user_id} started anon chat with target {target_id}")

        except ValueError:
            await update.message.reply_text("Noma'lum '/start' formati. Iltimos, faqat maxsus havoladan foydalaning.")
            
    else:
        # Oddiy /start buyrug'i
        anon_link = f"t.me/{bot_username}?start={user_id}"
        await update.message.reply_text(
            "👋 Salom! Men anonim chat bot.\n\n"
            "**🔗 Sizning maxfiy havolangiz:**\n"
            f"`{anon_link}`\n\n"
            "Bu havolani do'stingizga yuboring. U bosganda, sizga anonim yozishni boshlaydi.\n\n"
            "**Xabarlarga javob berish uchun xabarga REPLAY bosing!**",
            parse_mode='Markdown'
        )

# Xabarlarni boshqarish
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Kelgan xabarni anonim yuborish yoki javob (Reply) sifatida yuborish uchun ishlatiladi.
    """
    if not update.message:
        return

    sender_id = update.message.from_user.id
    
    # 1. REPLY (Javob berish) holatini tekshirish
    if update.message.reply_to_message:
        replied_msg_id = update.message.reply_to_message.message_id
        original_sender_id = ANON_REPLY_MAP.get(replied_msg_id)
        
        if original_sender_id:
            # Agar bu anonim xabarga berilgan javob bo'lsa
            
            # Original jo'natuvchiga anonim javobni yuborish
            try:
                # Xabar nusxasini yuborish (rasm, stiker, matn farqi yo'q)
                await update.message.copy(chat_id=original_sender_id)
                
                # Qabul qiluvchiga tasdiqlash xabari
                await update.message.reply_text(
                    "Javobingiz anonim tarzda yuborildi ✅",
                    quote=True 
                )
                logger.info(f"Reply from {sender_id} sent to original sender {original_sender_id}")
            except Exception as e:
                logger.error(f"Reply yuborishda xato: {e}")
                await update.message.reply_text("❌ Javob yuborilmadi (foydalanuvchi botni bloklagan bo'lishi mumkin).")
                
            # Reply jarayoni yakunlandi
            return

    # 2. YANGI ANONIM XABAR holatini tekshirish (Deep Link orqali boshlangan)
    target_id = context.user_data.get('sending_to')
    
    if target_id:
        # Foydalanuvchi anonim xabar yuborish rejimida
        try:
            # Xabarni maqsadli foydalanuvchiga yuborish
            # Xabarni ko'chirish (copy) rasm, video va stikerlarni qo'llab-quvvatlaydi.
            sent_message = await update.message.copy(
                chat_id=target_id,
                caption=update.message.caption or "📩 **Sizga anonim xabar keldi.**\n\n**Javob berish uchun Reply bosing!**",
                parse_mode='Markdown'
            )
            
            # Javob berish uchun xaritalashni saqlash (MUHIM: Bu qism DBsiz ishlamaydi!)
            ANON_REPLY_MAP[sent_message.message_id] = sender_id
            
            await update.message.reply_text("✅ Xabaringiz anonim tarzda yuborildi!")
            logger.info(f"Anon message from {sender_id} sent to target {target_id}. Map stored.")
            
            # Bir martalik yuborishdan keyin maqsadni tozalash (agar siz uni uzluksiz chat qilishni xohlamasangiz)
            # Agar siz suhbat uzluksiz davom etishini xohlasangiz, quyidagi qatorni o'chiring:
            # del context.user_data['sending_to']

        except Exception as e:
            logger.error(f"Anonim xabar yuborishda xato: {e}")
            await update.message.reply_text(
                "❌ Xabar yuborishda xato yuz berdi. Foydalanuvchi botni bloklagan bo'lishi mumkin."
            )
            
    else:
        # Boshlanmagan suhbat, foydalanuvchiga ko'rsatma berish
        await update.message.reply_text(
            "❓ Tushunarsiz buyruq. Anonim xabar yuborish uchun avval do'stingizning maxsus havolasini bosing yoki '/start' buyrug'ini yuboring."
        )

def main():
    """Botni ishga tushiruvchi asosiy funksiya."""
    
    # --------------------------------------------------------------------------------
    # MUHIM: Doimiy ma'lumotlar bazasi (DB) kerak!
    # Hozirgi holatda (ANON_REPLY_MAP lug'ati bilan) bot qayta ishga tushganda,
    # foydalanuvchilar orasidagi barcha REPLY imkoniyatlari yo'qoladi.
    # Bu real loyiha uchun yomon. Firestore (yoki boshqa DB) integratsiyasi shart.
    # --------------------------------------------------------------------------------

    application = ApplicationBuilder().token(TOKEN).build()

    # Kommandalarni o'rnatish
    application.add_handler(CommandHandler("start", start_command))

    # Barcha xabarlarni o'rnatish (rasm, matn, stiker)
    # Eslatma: filters.ALL barcha turdagi xabarlarni qamrab oladi.
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    logger.info("Bot ishga tushirilmoqda (Polling rejimida).")
    
    # Render.com'da bu qism Webhook orqali ishlashi mumkin. 
    # Agar Polling orqali ishlatayotgan bo'lsangiz, quyidagi qator qoladi:
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
