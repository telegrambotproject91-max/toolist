from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Task", callback_data="add_task")],
        [InlineKeyboardButton("📋 My Tasks", callback_data="my_tasks")],
        [InlineKeyboardButton("⏰ Reminders", callback_data="reminders")],
        [InlineKeyboardButton("✅ Completed Tasks", callback_data="completed")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton("❓ Help", callback_data="help_menu")]
    ])

def back_button(callback_data="main_menu"):
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data=callback_data)]])

def task_actions(task_id: int, done: bool = False):
    """Buttons for a single task in the list."""
    if done:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Undo", callback_data=f"undo_{task_id}"),
             InlineKeyboardButton("🗑 Delete", callback_data=f"delete_{task_id}")]
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Done", callback_data=f"done_{task_id}"),
             InlineKeyboardButton("✏️ Edit", callback_data=f"edit_{task_id}")],
            [InlineKeyboardButton("⏰ Remind", callback_data=f"remind_{task_id}"),
             InlineKeyboardButton("🗑 Delete", callback_data=f"delete_{task_id}")]
        ])

def reminder_actions(reminder_id: int):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancel Reminder", callback_data=f"cancel_reminder_{reminder_id}")]
    ])
