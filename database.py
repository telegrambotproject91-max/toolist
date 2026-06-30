import sqlite3
from datetime import datetime
from config import DATABASE_NAME

def get_connection():
    conn = sqlite3.connect(DATABASE_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            done BOOLEAN DEFAULT 0
        )
    """)
    cur.execute("""
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

# ---------- Task CRUD ----------
def add_task(user_id: int, description: str) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO tasks (user_id, description) VALUES (?, ?)", (user_id, description))
    conn.commit()
    task_id = cur.lastrowid
    conn.close()
    return task_id

def get_tasks(user_id: int, done: bool = None) -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    if done is None:
        cur.execute("SELECT id, description, done FROM tasks WHERE user_id = ? ORDER BY created_at", (user_id,))
    else:
        cur.execute("SELECT id, description, done FROM tasks WHERE user_id = ? AND done = ? ORDER BY created_at",
                    (user_id, int(done)))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def mark_task_done(task_id: int, user_id: int, done: bool = True) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET done = ? WHERE id = ? AND user_id = ?", (int(done), task_id, user_id))
    success = cur.rowcount > 0
    if done:
        # Remove any pending reminders for this task
        cur.execute("DELETE FROM reminders WHERE task_id = ? AND sent = 0", (task_id,))
    conn.commit()
    conn.close()
    return success

def delete_task(task_id: int, user_id: int) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM reminders WHERE task_id = ?", (task_id,))
    cur.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
    success = cur.rowcount > 0
    conn.commit()
    conn.close()
    return success

def clear_all_tasks(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM reminders WHERE task_id IN (SELECT id FROM tasks WHERE user_id = ?)", (user_id,))
    cur.execute("DELETE FROM tasks WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def update_task_description(task_id: int, user_id: int, new_desc: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET description = ? WHERE id = ? AND user_id = ?", (new_desc, task_id, user_id))
    ok = cur.rowcount > 0
    conn.commit()
    conn.close()
    return ok

# ---------- Reminders ----------
def add_reminder(task_id: int, remind_time: datetime) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO reminders (task_id, remind_time) VALUES (?, ?)",
                (task_id, remind_time.strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    rid = cur.lastrowid
    conn.close()
    return rid

def get_upcoming_reminders(user_id: int) -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT r.id, r.task_id, t.description, r.remind_time
        FROM reminders r
        JOIN tasks t ON r.task_id = t.id
        WHERE t.user_id = ? AND r.sent = 0
        ORDER BY r.remind_time
    """, (user_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def cancel_reminder(reminder_id: int, user_id: int) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM reminders
        WHERE id = ? AND task_id IN (SELECT id FROM tasks WHERE user_id = ?)
    """, (reminder_id, user_id))
    ok = cur.rowcount > 0
    conn.commit()
    conn.close()
    return ok

def get_pending_reminders() -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, task_id, remind_time FROM reminders WHERE sent = 0")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def mark_reminder_sent(reminder_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE reminders SET sent = 1 WHERE id = ?", (reminder_id,))
    conn.commit()
    conn.close()

def get_reminder_details(reminder_id: int) -> dict | None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT r.id, t.user_id, t.description
        FROM reminders r JOIN tasks t ON r.task_id = t.id
        WHERE r.id = ?
    """, (reminder_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None
