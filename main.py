import asyncio
import signal
import logging
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ConversationHandler
)
from config import BOT_TOKEN
from database import init_db
from handlers import (
    start, help_command, settings_menu,
    add_task_start, add_task_receive,
    edit_task_start, edit_task_receive,
    remind_task_start, remind_task_receive,
    cancel, my_tasks, task_actions_handler,
    mark_done, delete_task, reminders_list,
    cancel_reminder_handler, completed_tasks,
    unknown, add_cmd, list_cmd, reminders_cmd
)
from scheduler import start_scheduler, scheduler

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    # Conversation handler for multi-step flows
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(add_task_start, pattern="^add_task$"),
            CallbackQueryHandler(edit_task_start, pattern="^edit_(\d+)$"),
            CallbackQueryHandler(remind_task_start, pattern="^remind_(\d+)$"),
        ],
        states={
            0: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_task_receive)],
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_task_receive)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, remind_task_receive)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(cancel, pattern="^cancel$")
        ]
    )

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("add", add_cmd))
    app.add_handler(CommandHandler("list", list_cmd))
    app.add_handler(CommandHandler("reminders", reminders_cmd))
    app.add_handler(CommandHandler("completed", completed_tasks))

    # Callback query handlers (non-conversation)
    app.add_handler(CallbackQueryHandler(show_main_menu, pattern="^main_menu$"))  # needed? No, but we can add a back to main.
    # Actually the back button uses "main_menu" callback, we need a handler that sends the main menu.
    # We'll define a simple function to edit to main menu.
    from keyboards import main_menu as main_menu_keyboard
    async def main_menu_callback(update, context):
        await update.callback_query.edit_message_text(
            "👋 Welcome to <b>To Do List Bot</b>!\n\n"
            "I help you manage your tasks and never miss a deadline.\n"
            "Use the menu below:",
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML"
        )
    app.add_handler(CallbackQueryHandler(main_menu_callback, pattern="^main_menu$"))
    app.add_handler(CallbackQueryHandler(help_command, pattern="^help_menu$"))
    app.add_handler(CallbackQueryHandler(settings_menu, pattern="^settings$"))
    app.add_handler(CallbackQueryHandler(my_tasks, pattern="^my_tasks$"))
    app.add_handler(CallbackQueryHandler(reminders_list, pattern="^reminders$"))
    app.add_handler(CallbackQueryHandler(completed_tasks, pattern="^completed$"))
    app.add_handler(CallbackQueryHandler(task_actions_handler, pattern="^actions_(\d+)$"))
    app.add_handler(CallbackQueryHandler(mark_done, pattern="^done_(\d+)$"))
    app.add_handler(CallbackQueryHandler(lambda u,c: mark_done(u,c,done=False), pattern="^undo_(\d+)$"))
    app.add_handler(CallbackQueryHandler(delete_task, pattern="^delete_(\d+)$"))
    app.add_handler(CallbackQueryHandler(cancel_reminder_handler, pattern="^cancel_reminder_(\d+)$"))
    app.add_handler(conv_handler)
    # Fallback for unknown messages (must be last)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown))

    start_scheduler(app.bot)

    async with app:
        await app.start()
        await app.updater.start_polling()
        stop_event = asyncio.Event()
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGINT, stop_event.set)
        loop.add_signal_handler(signal.SIGTERM, stop_event.set)
        logger.info("Bot started.")
        await stop_event.wait()

    scheduler.shutdown(wait=False)

if __name__ == "__main__":
    asyncio.run(main())
