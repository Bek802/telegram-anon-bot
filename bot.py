import random
import string
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8349538809:AAH99J3Wa0tR3WmEDqTrlXmEy-NpSDoA0MQ"

# ID ↔ User mapping
user_links = {}
link_to_user = {}

# Tasodifiy link generatsiya qilish
def generate_link():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

# /start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Foydalanuvchi uchun link yaratamiz (agar oldin yaratilmagan bo‘lsa)
    if user_id not in user_links:
        link = generate_link()
        user_links[user_id] = link
        link_to_user[link] = user_id
    else:
        link = user_links[user_id]

    msg = (
        "👋 Salom! Bu anonim chat bot.\n\n"
        "🔗 Sizning maxfiy linkingiz:\n"
        f"`{link}`\n\n"
        "➡️ Bu kodni guruh yoki do‘stlaringizga bering. "
        "Kimdir shu kodni yozsa, sizga anonim xabar yuborishi mumkin."
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

# Oddiy xabarlarni ushlash
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # Agar xabar link bo‘lsa
    if text in link_to_user:
        target_user = link_to_user[text]
        context.user_data["sending_to"] = target_user
        await update.message.reply_text("✍️ Endi xabar yozing, u anonim tarzda yuboriladi!")
        return

    # Agar foydalanuvchi boshqa odamga anonim xabar yuborayotgan bo‘lsa
    if "sending_to" in context.user_data:
        target_user = context.user_data["sending_to"]
        try:
            await context.bot.send_message(
                chat_id=target_user,
                text=f"📩 Sizga anonim xabar keldi:\n\n{text}"
            )
            await update.message.reply_text("✅ Xabaringiz anonim yuborildi!")
        except:
            await update.message.reply_text("❌ Xabar yuborilmadi (foydalanuvchi botni bloklagan bo‘lishi mumkin).")

        # Bir martalik bo‘lishi uchun tozalaymiz
        del context.user_data["sending_to"]

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
