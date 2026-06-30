from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Bot
import database as db

# Global scheduler instance
scheduler = BackgroundScheduler()

def send_reminder(bot: Bot, reminder_id: int):
    """Job function: send the reminder message and mark it sent."""
    details = db.get_reminder_details(reminder_id)
    if details is None:
        return  # task already deleted
    user_id = details["user_id"]
    description = details["description"]
    try:
        bot.send_message(
            chat_id=user_id,
            text=f"⏰ Reminder: {description}"
        )
        db.mark_reminder_sent(reminder_id)
    except Exception as e:
        print(f"Failed to send reminder {reminder_id}: {e}")

def schedule_single_reminder(bot: Bot, reminder_id: int, run_date: datetime):
    """Add a single reminder job to the scheduler."""
    scheduler.add_job(
        send_reminder,
        'date',
        run_date=run_date,
        args=[bot, reminder_id],
        misfire_grace_time=60,  # allow 1 minute delay
        id=str(reminder_id)     # prevent duplicate jobs
    )

def load_pending_reminders(bot: Bot):
    """Load all unsent reminders from the database and schedule them."""
    reminders = db.get_pending_reminders()
    for rem in reminders:
        remind_time = datetime.strptime(rem["remind_time"], "%Y-%m-%d %H:%M:%S")
        schedule_single_reminder(bot, rem["id"], remind_time)

def start_scheduler(bot: Bot):
    """Start the background scheduler and load existing reminders."""
    load_pending_reminders(bot)
    scheduler.start()
