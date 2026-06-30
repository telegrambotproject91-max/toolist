import asyncio
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from config import BOT_TOKEN
from database import init_db
from handlers import (
    start, help_command, add_task, list_tasks,
    done_task, delete_task_cmd, clear_tasks, remind_task,
    button_callback
)
from scheduler import start_scheduler


def main():
    # Initialize the database
    init_db()

    # Build the application
    application = Application.builder().token(BOT_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("add", add_task))
    application.add_handler(CommandHandler("list", list_tasks))
    application.add_handler(CommandHandler("done", done_task))
    application.add_handler(CommandHandler("delete", delete_task_cmd))
    application.add_handler(CommandHandler("clear", clear_tasks))
    application.add_handler(CommandHandler("remind", remind_task))

    # Register callback query handler for inline buttons
    application.add_handler(CallbackQueryHandler(button_callback))

    # Start the reminder scheduler (pass the bot instance)
    start_scheduler(application.bot)

    # ---- FIX for Python 3.14 ----
    # Create a new event loop and set it as the current loop.
    # This prevents the RuntimeError: "There is no current event loop"
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Start polling
    print("Bot is running...")
    application.run_polling()


if __name__ == "__main__":
    main()
