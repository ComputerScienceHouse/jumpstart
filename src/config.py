import os
import json
from dotenv import load_dotenv


load_dotenv()

BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))

SLACK_API_TOKEN: str | None = os.getenv("SLACK_API_TOKEN", None)
SLACK_JUMPSTART_MESSAGE: str = "Would you like to post this message to Jumpstart?"
WATCHED_CHANNELS: tuple[str] = tuple(os.getenv("WATCHED_CHANNELS", "").split(","))
SLACK_DM_TEMPLATE: dict | None = None

CALENDAR_URL: str | None = os.getenv("CALENDAR_URL", None)
CALENDAR_OUTLOOK_DAYS: int = int(os.getenv("CALENDAR_OUTLOOK_DAYS", "7"))
CALENDAR_EVENT_MAXIMUM: int = int(os.getenv("CALENDAR_EVENT_MAXIMUM", "10"))
CALENDAR_TIMEZONE: str = os.getenv("CALENDAR_TIMEZONE", "America/New_York")
CALENDAR_CACHE_REFRESH: int = int(os.getenv("CALENDAR_CACHE_REFRESH", "10"))

if SLACK_API_TOKEN in (None, ""):
	raise Exception("Missing SLACK_API_TOKEN")

with open(os.path.join(BASE_DIR, "static", "slack", "dm_request_template.json")) as f:
	SLACK_DM_TEMPLATE = json.load(f)
