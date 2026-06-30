# Telegram To Do List Bot

A full‑featured, multi‑user task manager with reminders and a polished inline‑keyboard UI.

## Features
- **Main menu** with all actions accessible via buttons.
- **Add, edit, delete tasks** with multi‑step conversations.
- **Set reminders** for any task; notification sent exactly at the scheduled time.
- **View active tasks**, completed tasks, and upcoming reminders.
- **Undo** completed tasks.
- All data stored in SQLite; supports multiple users.

## Local Run
1. Clone the repo.
2. Install dependencies: `pip install -r requirements.txt`
3. Set your bot token in `config.py` (or via environment variable `BOT_TOKEN`).
4. Run: `python main.py`

## Deploy on Render
1. Push to GitHub.
2. On Render, create a new **Background Worker**, connect the repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `python main.py`
5. Add environment variable `BOT_TOKEN` with your bot token.
6. Deploy!
