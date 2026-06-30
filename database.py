import sqlite3
from datetime import datetime
from config import DATABASE_NAME

def get_connection():
    """Create a new database connection (check_same_thread=False for multi‑thread safety)."""
    conn = sqlite3.connect(DATABASE_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            done BOOLEAN DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            remind_time TIMESTAMP NOT NULL,
            sent BOOLEAN DEFAULT 0,
            FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()

# ---------- Task operations ----------

def add_task(user_id: int, description: str) -> int:
    """Add a new task and return its ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (user_id, description) VALUES (?, ?)",
        (user_id, description)
    )
    conn.commit()
    task_id = cursor.lastrowid
    conn.close()
    return task_id

def get_tasks(user_id: int) -> list[dict]:
    """Return all tasks of a user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, description, done FROM tasks WHERE user_id = ? ORDER BY created_at",
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def mark_task_done(task_id: int, user_id: int) -> bool:
    """Mark a task as done. Return True if successful."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tasks SET done = 1 WHERE id = ? AND user_id = ? AND done = 0",
        (task_id, user_id)
    )
    success = cursor.rowcount > 0
    # Remove any pending reminders for this task
    if success:
        cursor.execute("DELETE FROM reminders WHERE task_id = ? AND sent = 0", (task_id,))
    conn.commit()
    conn.close()
    return success

def delete_task(task_id: int, user_id: int) -> bool:
    """Delete a task and its reminders. Return True if the task existed and belonged to the user."""
    conn = get_connection()
    cursor = conn.cursor()
    # First delete reminders (cascade may not be enabled, so delete manually)
    cursor.execute("DELETE FROM reminders WHERE task_id = ?", (task_id,))
    cursor.execute(
        "DELETE FROM tasks WHERE id = ? AND user_id = ?",
        (task_id, user_id)
    )
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

def clear_all_tasks(user_id: int):
    """Delete all tasks (and their reminders) for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    # Delete all reminders that belong to tasks of this user
    cursor.execute("""
        DELETE FROM reminders WHERE task_id IN (
            SELECT id FROM tasks WHERE user_id = ?
        )
    """, (user_id,))
    cursor.execute("DELETE FROM tasks WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# ---------- Reminder operations ----------

def add_reminder(task_id: int, remind_time: datetime) -> int:
    """Store a new reminder. Return the reminder ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO reminders (task_id, remind_time) VALUES (?, ?)",
        (task_id, remind_time.strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    reminder_id = cursor.lastrowid
    conn.close()
    return reminder_id

def get_pending_reminders() -> list[dict]:
    """Return all reminders that are not yet sent and whose time is in the future."""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "SELECT id, task_id, remind_time FROM reminders WHERE sent = 0 AND remind_time > ?",
        (now,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def mark_reminder_sent(reminder_id: int):
    """Mark a reminder as sent."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE reminders SET sent = 1 WHERE id = ?", (reminder_id,))
    conn.commit()
    conn.close()

def get_reminder_details(reminder_id: int) -> dict | None:
    """Get task description and user_id for a reminder."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.id, t.user_id, t.description
        FROM reminders r
        JOIN tasks t ON r.task_id = t.id
        WHERE r.id = ?
    """, (reminder_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None
