import os
import sys
import logging

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


logging.basicConfig(level=logging.INFO)


async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')


def get_token() -> str:
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        logging.error("Environment variable TELEGRAM_TOKEN is not set.")
        return ""
    return token


TOKEN = get_token()
if not TOKEN:
    # If the token is missing, avoid building the app to prevent accidental network calls on import.
    # Exiting with code 1 makes the failure explicit when running the module directly.
    if __name__ == "__main__":
        sys.exit(1)

app = ApplicationBuilder().token(TOKEN).build() if TOKEN else None

if app:
    app.add_handler(CommandHandler("hello", hello))


if __name__ == "__main__":
    if not app:
        logging.error("Bot not started because token is missing.")
        sys.exit(1)
    logging.info("Starting Telegram bot polling...")
    app.run_polling()