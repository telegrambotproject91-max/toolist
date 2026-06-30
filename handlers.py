from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

import database as db
from config import DATETIME_FORMAT
from scheduler import schedule_single_reminder

# ---------- Helper to escape HTML ----------
def escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# ---------- /start ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to the To‑Do Bot!\n\n"
        "Commands:\n"
        "/add <text> – add a new task\n"
        "/list – show your tasks\n"
        "/done <id> – mark a task as done\n"
        "/delete <id> – delete a task\n"
        "/clear – remove all tasks (with confirmation)\n"
        "/remind <task_id> YYYY‑MM‑DD HH:MM – set a reminder\n"
        "/help – show this message"
    )

# ---------- /help ----------
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

# ---------- /add ----------
async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not context.args:
        await update.message.reply_text("ℹ️ Usage: /add <task description>")
        return
    description = " ".join(context.args)
    task_id = db.add_task(user.id, description)
    await update.message.reply_text(f"✅ Task #{task_id} added: {escape_html(description)}", parse_mode="HTML")

# ---------- /list ----------
async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    tasks = db.get_tasks(user.id)
    if not tasks:
        await update.message.reply_text("📭 You have no tasks.")
        return

    text_lines = []
    keyboard = []
    for t in tasks:
        task_id = t["id"]
        desc = escape_html(t["description"])
        if t["done"]:
            # strikethrough for completed tasks
            text_lines.append(f"✅ <s>{task_id}. {desc}</s>")
        else:
            text_lines.append(f"❌ {task_id}. {desc}")
            keyboard.append([
                InlineKeyboardButton("✅ Done", callback_data=f"done_{task_id}"),
                InlineKeyboardButton("🗑 Delete", callback_data=f"delete_{task_id}")
            ])

    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    await update.message.reply_text(
        "\n".join(text_lines),
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

# ---------- /done (command fallback) ----------
async def done_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not context.args:
        await update.message.reply_text("ℹ️ Usage: /done <task_id>")
        return
    try:
        task_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("⚠️ Task ID must be a number.")
        return

    if db.mark_task_done(task_id, user.id):
        await update.message.reply_text(f"✅ Task #{task_id} marked as done.")
    else:
        await update.message.reply_text("❌ Task not found or already completed.")

# ---------- /delete (command fallback) ----------
async def delete_task_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not context.args:
        await update.message.reply_text("ℹ️ Usage: /delete <task_id>")
        return
    try:
        task_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("⚠️ Task ID must be a number.")
        return

    if db.delete_task(task_id, user.id):
        await update.message.reply_text(f"🗑 Task #{task_id} deleted.")
    else:
        await update.message.reply_text("❌ Task not found.")

# ---------- /clear ----------
async def clear_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes, delete all", callback_data="clear_yes"),
            InlineKeyboardButton("❌ No", callback_data="clear_no")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "⚠️ Are you sure you want to delete all your tasks?",
        reply_markup=reply_markup
    )

# ---------- /remind ----------
async def remind_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if len(context.args) < 3:
        await update.message.reply_text(
            "ℹ️ Usage: /remind <task_id> YYYY-MM-DD HH:MM\n"
            "Example: /remind 1 2025-12-31 14:30"
        )
        return

    try:
        task_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("⚠️ Task ID must be a number.")
        return

    # Check that the task exists and belongs to the user
    tasks = db.get_tasks(user.id)
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        await update.message.reply_text("❌ Task not found.")
        return

    # Parse date/time
    date_str = context.args[1]
    time_str = context.args[2]
    try:
        remind_dt = datetime.strptime(f"{date_str} {time_str}", DATETIME_FORMAT)
    except ValueError:
        await update.message.reply_text(
            f"⚠️ Invalid date/time format. Use YYYY-MM-DD HH:MM (24‑hour).\n"
            f"Example: 2025-12-31 14:30"
        )
        return

    if remind_dt <= datetime.now():
        await update.message.reply_text("⚠️ Reminder time must be in the future.")
        return

    # Store the reminder
    reminder_id = db.add_reminder(task_id, remind_dt)
    # Schedule the job immediately
    schedule_single_reminder(context.application.bot, reminder_id, remind_dt)

    await update.message.reply_text(
        f"⏰ Reminder set for task #{task_id} at {remind_dt.strftime(DATETIME_FORMAT)}."
    )

# ---------- Callback query handler (inline buttons) ----------
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # acknowledge
    user = query.from_user
    data = query.data

    if data.startswith("done_"):
        task_id = int(data.split("_")[1])
        if db.mark_task_done(task_id, user.id):
            await query.edit_message_text(
                f"✅ Task #{task_id} marked as done.",
                parse_mode="HTML"
            )
        else:
            await query.edit_message_text("❌ Task not found or already completed.")
    elif data.startswith("delete_"):
        task_id = int(data.split("_")[1])
        if db.delete_task(task_id, user.id):
            await query.edit_message_text(f"🗑 Task #{task_id} deleted.")
        else:
            await query.edit_message_text("❌ Task not found.")
    elif data == "clear_yes":
        db.clear_all_tasks(user.id)
        await query.edit_message_text("🧹 All tasks have been deleted.")
    elif data == "clear_no":
        await query.edit_message_text("Cancelled – your tasks are safe.")
