from datetime import datetime
from config import DATETIME_FORMAT

def escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def format_datetime(dt: datetime | str) -> str:
    if isinstance(dt, str):
        dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
    return dt.strftime(DATETIME_FORMAT)

def parse_datetime(date_str: str, time_str: str) -> datetime | None:
    try:
        return datetime.strptime(f"{date_str} {time_str}", DATETIME_FORMAT)
    except ValueError:
        return None
