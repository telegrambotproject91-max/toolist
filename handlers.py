import logging
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ConversationHandler
)

import database as db
from scheduler import schedule_single_reminder
from keyboards import main_menu, back_button, task_actions, reminder_actions
from utils import escape_html, format_datetime, parse_datetime
from config import DATETIME_FORMAT

logger = logging.getLogger(__name__)

# Conversation states
ADD_TASK, EDIT_TASK, SET_REMINDER = range(3)

# ---------- Helper: send main menu ----------
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, edit=False):
    text = ("👋 Welcome to <b>To Do List Bot</b>!\n\n"
            "I help you manage your tasks and never miss a deadline.\n"
            "Use the menu below:")
    if edit and update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=main_menu(), parse_mode="HTML")
    elif update.message:
        await update.message.reply_text(text, reply_markup=main_menu(), parse_mode="HTML")

# ---------- /start ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_main_menu(update, context)

# ---------- /help command & callback ----------
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🔹 <b>Commands & Tips</b>\n\n"
        "• Use the menu buttons for quick actions.\n"
        "• You can also type /add to add a task directly.\n"
        "• /list – show active tasks\n"
        "• /reminders – upcoming reminders\n"
        "• /completed – finished tasks\n"
        "• /settings – app settings\n"
        "• /help – this message"
    )
    if update.callback_query:
        await update.callback_query.edit_message_text(help_text, reply_markup=back_button(), parse_mode="HTML")
    else:
        await update.message.reply_text(help_text, reply_markup=back_button(), parse_mode="HTML")

# ---------- Settings (stub) ----------
async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_text(
        "⚙️ <b>Settings</b>\n\nNo additional settings available right now. Stay tuned!",
        reply_markup=back_button(),
        parse_mode="HTML"
    )

# ---------- Add Task conversation ----------
async def add_task_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📝 <b>Add Task</b>\nSend me the task description:", parse_mode="HTML")
    return ADD_TASK

async def add_task_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    description = update.message.text.strip()
    if len(description) < 1:
        await update.message.reply_text("⚠️ Description cannot be empty. Try again.")
        return ADD_TASK
    task_id = db.add_task(user.id, description)
    await update.message.reply_text(
        f"✅ Task #{task_id} added: {escape_html(description)}",
        parse_mode="HTML",
        reply_markup=main_menu()
    )
    return ConversationHandler.END

# ---------- Edit Task conversation ----------
async def edit_task_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    task_id = int(query.data.split("_")[1])
    context.user_data["edit_task_id"] = task_id
    await query.edit_message_text("✏️ Send me the new description for this task:")
    return EDIT_TASK

async def edit_task_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    task_id = context.user_data.get("edit_task_id")
    if not task_id:
        await update.message.reply_text("⚠️ Something went wrong. Please start again.", reply_markup=main_menu())
        return ConversationHandler.END
    new_desc = update.message.text.strip()
    if not new_desc:
        await update.message.reply_text("⚠️ Description cannot be empty. Send a new description or /cancel.")
        return EDIT_TASK
    if db.update_task_description(task_id, user.id, new_desc):
        await update.message.reply_text("✅ Task updated.", reply_markup=main_menu())
    else:
        await update.message.reply_text("❌ Could not update the task.", reply_markup=main_menu())
    return ConversationHandler.END

# ---------- Set Reminder conversation ----------
async def remind_task_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    task_id = int(query.data.split("_")[1])
    # Verify task exists
    tasks = db.get_tasks(query.from_user.id, done=False)
    if not any(t["id"] == task_id for t in tasks):
        await query.edit_message_text("❌ Task not found or already completed.", reply_markup=main_menu())
        return ConversationHandler.END
    context.user_data["remind_task_id"] = task_id
    await query.edit_message_text(
        "⏰ <b>Set Reminder</b>\nSend the date and time in format: <code>YYYY-MM-DD HH:MM</code>\n"
        "Example: 2025-12-31 14:30",
        parse_mode="HTML"
    )
    return SET_REMINDER

async def remind_task_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    task_id = context.user_data.get("remind_task_id")
    if not task_id:
        await update.message.reply_text("⚠️ Session expired. Please start again.", reply_markup=main_menu())
        return ConversationHandler.END

    parts = update.message.text.strip().split()
    if len(parts) != 2:
        await update.message.reply_text("⚠️ Format: YYYY-MM-DD HH:MM. Example: 2025-12-31 14:30")
        return SET_REMINDER

    remind_dt = parse_datetime(parts[0], parts[1])
    if not remind_dt:
        await update.message.reply_text("⚠️ Invalid date/time. Use format: YYYY-MM-DD HH:MM")
        return SET_REMINDER
    if remind_dt <= datetime.now():
        await update.message.reply_text("⚠️ Reminder time must be in the future.")
        return SET_REMINDER

    reminder_id = db.add_reminder(task_id, remind_dt)
    schedule_single_reminder(context.application.bot, reminder_id, remind_dt)
    await update.message.reply_text(
        f"⏰ Reminder set for {format_datetime(remind_dt)}.",
        reply_markup=main_menu()
    )
    return ConversationHandler.END

# ---------- Cancel conversation ----------
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.edit_message_text("❎ Cancelled.", reply_markup=main_menu())
    else:
        await update.message.reply_text("❎ Cancelled.", reply_markup=main_menu())
    return ConversationHandler.END

# ---------- My Tasks ----------
async def my_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    tasks = db.get_tasks(user.id, done=False)
    if not tasks:
        await query.edit_message_text("📭 No active tasks. Add one with ➕ Add Task.", reply_markup=back_button())
        return
    text_lines = ["<b>📋 Active Tasks</b>\n"]
    for t in tasks:
        desc = escape_html(t["description"])
        text_lines.append(f"• <b>#{t['id']}</b> {desc}")
    await query.edit_message_text(
        "\n".join(text_lines),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(str(t["id"]), callback_data=f"actions_{t['id']}")] for t in tasks
        ] + [[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]])
    )
    # Store the task list in user_data for later reference (optional)
    context.user_data["task_list"] = [t["id"] for t in tasks]

# ---------- Show actions for a specific task ----------
async def task_actions_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    task_id = int(query.data.split("_")[1])
    user = query.from_user
    # Fetch task to verify and get description
    tasks = db.get_tasks(user.id)  # get all
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        await query.edit_message_text("❌ Task not found.", reply_markup=back_button())
        return
    desc = escape_html(task["description"])
    done = task["done"]
    status = "✅ Completed" if done else "❌ Active"
    text = f"<b>Task #{task_id}</b> – {status}\n{desc}"
    await query.edit_message_text(text, reply_markup=task_actions(task_id, done), parse_mode="HTML")

# ---------- Task done / undo ----------
async def mark_done(update: Update, context: ContextTypes.DEFAULT_TYPE, done: bool = True):
    query = update.callback_query
    await query.answer()
    task_id = int(query.data.split("_")[1])
    user = query.from_user
    if db.mark_task_done(task_id, user.id, done):
        new_status = "completed" if done else "reopened"
        await query.edit_message_text(f"✅ Task #{task_id} marked as {new_status}.", reply_markup=back_button())
    else:
        await query.edit_message_text("❌ Could not update task.", reply_markup=back_button())

# ---------- Delete task ----------
async def delete_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    task_id = int(query.data.split("_")[1])
    user = query.from_user
    if db.delete_task(task_id, user.id):
        await query.edit_message_text(f"🗑 Task #{task_id} deleted.", reply_markup=back_button())
    else:
        await query.edit_message_text("❌ Task not found.", reply_markup=back_button())

# ---------- Reminders list ----------
async def reminders_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    reminders = db.get_upcoming_reminders(user.id)
    if not reminders:
        await query.edit_message_text("🔔 No upcoming reminders.", reply_markup=back_button())
        return
    lines = ["<b>⏰ Upcoming Reminders</b>\n"]
    for r in reminders:
        desc = escape_html(r["description"])
        rtime = format_datetime(r["remind_time"])
        lines.append(f"• <b>Task #{r['task_id']}</b>: {desc} at {rtime}")
        lines.append(f"  └ [Cancel](callback:cancel_reminder_{r['id']})")
    await query.edit_message_text("\n".join(lines), parse_mode="HTML",
                                  reply_markup=InlineKeyboardMarkup([
                                      [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
                                  ]))

# ---------- Cancel reminder ----------
async def cancel_reminder_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    reminder_id = int(query.data.split("_")[2])
    user = query.from_user
    if db.cancel_reminder(reminder_id, user.id):
        await query.edit_message_text("✅ Reminder cancelled.", reply_markup=back_button())
    else:
        await query.edit_message_text("❌ Could not cancel reminder.", reply_markup=back_button())

# ---------- Completed tasks ----------
async def completed_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    tasks = db.get_tasks(user.id, done=True)
    if not tasks:
        await query.edit_message_text("✅ No completed tasks yet.", reply_markup=back_button())
        return
    text_lines = ["<b>✅ Completed Tasks</b>\n"]
    for t in tasks:
        desc = escape_html(t["description"])
        text_lines.append(f"• <b>#{t['id']}</b> {desc}")
    await query.edit_message_text("\n".join(text_lines), parse_mode="HTML",
                                  reply_markup=InlineKeyboardMarkup([
                                      [InlineKeyboardButton(str(t["id"]), callback_data=f"actions_{t['id']}")] for t in tasks
                                  ] + [[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]))

# ---------- Fallback for unknown commands ----------
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤔 I didn't understand that. Use the menu below:", reply_markup=main_menu())

# ---------- Legacy commands (optional direct access) ----------
async def add_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not context.args:
        await update.message.reply_text("Usage: /add <task description>")
        return
    desc = " ".join(context.args)
    tid = db.add_task(user.id, desc)
    await update.message.reply_text(f"✅ Task #{tid} added.", reply_markup=main_menu())

async def list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tasks = db.get_tasks(update.effective_user.id, done=False)
    if not tasks:
        await update.message.reply_text("No active tasks.")
        return
    text = "\n".join(f"#{t['id']} {t['description']}" for t in tasks)
    await update.message.reply_text(text, reply_markup=main_menu())

async def reminders_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reminders = db.get_upcoming_reminders(update.effective_user.id)
    if not reminders:
        await update.message.reply_text("No reminders.")
        return
    text = "\n".join(f"Task #{r['task_id']} at {format_datetime(r['remind_time'])}" for r in reminders)
    await update.message.reply_text(text, reply_markup=main_menu())
