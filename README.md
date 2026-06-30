# Telegram To‑Do List Bot

A simple, multi‑user Telegram bot for managing tasks with reminders.

## Features
- `/add` – add a task
- `/list` – view tasks with inline **Done** and **Delete** buttons
- `/done <id>` – mark a task as completed
- `/delete <id>` – delete a task
- `/clear` – delete all tasks (with confirmation)
- `/remind <task_id> YYYY-MM-DD HH:MM` – set a reminder
- Reminders are sent automatically using `APScheduler`

## Local Development

1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
