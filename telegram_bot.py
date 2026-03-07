import os
import sys
import logging
import asyncio

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# Use the project text detector
try:
    from image_detector import detect_fake_text
except Exception:
    detect_fake_text = None


logging.basicConfig(level=logging.INFO)


async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')


async def echo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Echo command: /echo some text
    args = context.args if hasattr(context, "args") else []
    text = " ".join(args).strip()
    if not text:
        await update.message.reply_text("Usage: /echo <some text>")
        return
    await update.message.reply_text(text)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Generic text handler for plain messages
    if not update.message or not update.message.text:
        return
    text = update.message.text
    # If a detector is available, run analysis; otherwise echo
    if detect_fake_text is not None:
        await update.message.reply_text("Analyzing text, please wait...")
        try:
            result = await asyncio.to_thread(detect_fake_text, text)
        except Exception as e:
            result = f"Detection error: {e}"
        await update.message.reply_text(result)
    else:
        await update.message.reply_text(f"You said: {text}")


async def detect_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # /detect <text>
    if detect_fake_text is None:
        await update.message.reply_text("Text detector is not available.")
        return

    args = context.args if hasattr(context, "args") else []
    text = " ".join(args).strip()
    if not text:
        await update.message.reply_text("Usage: /detect <text>")
        return

    await update.message.reply_text("Analyzing text, please wait...")
    try:
        result = await asyncio.to_thread(detect_fake_text, text)
    except Exception as e:
        result = f"Detection error: {e}"

    await update.message.reply_text(result)


def get_token() -> str:
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        logging.error("Environment variable TELEGRAM_TOKEN is not set.")
        return ""
    return token



def main_cli():
    """Run the text detector from the command line."""
    if detect_fake_text is None:
        print("Text detector not available.")
        sys.exit(1)

    # Check if text is provided as command-line arguments, excluding the script name and '--cli'
    args = [arg for arg in sys.argv[1:] if arg != '--cli']
    if args:
        text = " ".join(args).strip()
    else:
        try:
            text = input("Enter text to analyze: ").strip()
        except EOFError:
            text = ""

    if not text:
        print("No text provided. Exiting.")
        sys.exit(0)

    try:
        # The detector function might be synchronous
        result = detect_fake_text(text)
    except Exception as e:
        result = f"Detection error: {e}"

    print("=== Analysis Result ===")
    print(result)


def start_bot():
    """Initializes and starts the Telegram bot."""
    token = get_token()
    if not token:
        try:
            token = input("TELEGRAM_TOKEN not set. Enter token (or leave blank to exit): ").strip()
        except EOFError:
            token = ""
        if not token:
            logging.error("No TELEGRAM_TOKEN provided; exiting.")
            sys.exit(1)
        os.environ["TELEGRAM_TOKEN"] = token

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("hello", hello))
    app.add_handler(CommandHandler("echo", echo_command))
    app.add_handler(CommandHandler("detect", detect_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))

    logging.info("Starting Telegram bot polling...")
    app.run_polling()


if __name__ == "__main__":
    if '--cli' in sys.argv:
        main_cli()
    else:
        start_bot()