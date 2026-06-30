import os

# Bot token – read from environment variable in production,
# fallback to the provided token for local development.
BOT_TOKEN = os.getenv("BOT_TOKEN", "8951394856:AAGefa-CNfQ4gEjxDMZRq6AQuQRF47-EqUg")

# Database file name
DATABASE_NAME = "todo.db"

# Date/time format used for /remind
DATETIME_FORMAT = "%Y-%m-%d %H:%M"
