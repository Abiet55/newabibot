import logging
import os
import sys
from typing import Optional, cast
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from telegram.error import Conflict
from config import BOT_TOKEN
from handlers import (
    start,
    help_command,
    menu,
    handle_callback,
    handle_feedback,
    handle_admin_approval
)

# Enhanced logging configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)
PID_FILE = "bot.pid"

def check_pid(pid):
    """Check if a process with given PID is running."""
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True

def cleanup_pid_file():
    """Remove the PID file."""
    try:
        if os.path.exists(PID_FILE):
            os.unlink(PID_FILE)
    except Exception as e:
        logger.error(f"Error cleaning up PID file: {e}")

def write_pid_file():
    """Write current process PID to file."""
    try:
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
    except Exception as e:
        logger.error(f"Error writing PID file: {e}")
        sys.exit(1)

async def error_handler(update: Optional[object], context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    logger.error("Exception while handling an update:", exc_info=context.error)

    chat_id = None
    if isinstance(update, Update) and update.effective_chat:
        chat_id = update.effective_chat.id

    if isinstance(context.error, Conflict):
        logger.warning(f"Conflict error occurred for chat_id {chat_id}, another instance might be running")
        return

    if chat_id:
        try:
            text = "Sorry, I encountered an error while processing your request. Please try again later."
            await context.bot.send_message(chat_id=chat_id, text=text)
        except Exception as e:
            logger.error(f"Failed to send error message to user: {e}")

def main():
    """Start the bot."""
    # Check if another instance is running
    if os.path.exists(PID_FILE):
        with open(PID_FILE) as f:
            pid = int(f.read().strip())
            if check_pid(pid):
                logger.error(f"Another instance is already running with PID {pid}")
                sys.exit(1)
            else:
                cleanup_pid_file()

    # Write current PID
    write_pid_file()

    try:
        application = ApplicationBuilder().token(BOT_TOKEN).build()

        # Add command handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("menu", menu))


        # Admin approval handler
        application.add_handler(CallbackQueryHandler(
            handle_admin_approval,
            pattern="^(approve|reject)_"
        ))

        # Payment confirmation handler
        application.add_handler(CallbackQueryHandler(
            handle_callback,
            pattern="^(confirm_payment_|cancel_payment)"
        ))

        # General callback handler
        application.add_handler(CallbackQueryHandler(handle_callback))

        # Feedback handler
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_feedback
        ))

        # Error handler
        application.add_error_handler(error_handler)

        # Start the Bot
        logger.info("Starting bot...")
        application.run_polling(drop_pending_updates=True)
        logger.info("Bot stopped.")

    finally:
        # Clean up PID file when bot stops
        cleanup_pid_file()

if __name__ == '__main__':
    main()