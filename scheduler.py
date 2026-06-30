from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Bot
import database as db
import logging

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()

def send_reminder(bot: Bot, reminder_id: int):
    details = db.get_reminder_details(reminder_id)
    if not details:
        return
    try:
        bot.send_message(chat_id=details["user_id"], text=f"⏰ Reminder: {details['description']}")
        db.mark_reminder_sent(reminder_id)
    except Exception as e:
        logger.error(f"Failed to send reminder {reminder_id}: {e}")

def schedule_single_reminder(bot: Bot, reminder_id: int, run_date: datetime):
    scheduler.add_job(
        send_reminder,
        'date',
        run_date=run_date,
        args=[bot, reminder_id],
        misfire_grace_time=60,
        id=str(reminder_id)
    )

def load_pending_reminders(bot: Bot):
    reminders = db.get_pending_reminders()
    for rem in reminders:
        remind_time = datetime.strptime(rem["remind_time"], "%Y-%m-%d %H:%M:%S")
        schedule_single_reminder(bot, rem["id"], remind_time)

def start_scheduler(bot: Bot):
    load_pending_reminders(bot)
    scheduler.start()
