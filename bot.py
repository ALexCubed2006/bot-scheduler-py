# bot.py
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
PROXY_URL = os.getenv("PROXY_URL")

def main():
    builder = Application.builder().token(TOKEN)
    if PROXY_URL:
        builder = builder.proxy(PROXY_URL)
    app = builder.build()

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("hi")

    async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(update.message.text)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    print("running")
    app.run_polling()

if __name__ == "__main__":
    main()