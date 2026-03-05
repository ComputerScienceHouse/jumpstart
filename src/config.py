import os
from dotenv import load_dotenv


load_dotenv()

BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))

CALENDAR_URL: str | None = os.getenv("CALENDAR_URL", None)
CALENDAR_OUTLOOK_DAYS: int = int(os.getenv("CALENDAR_OUTLOOK_DAYS", "7"))
CALENDAR_EVENT_MAXIMUM: int = int(os.getenv("CALENDAR_EVENT_MAXIMUM", "10"))
CALENDAR_TIMEZONE: str = os.getenv("CALENDAR_TIMEZONE", "America/New_York")