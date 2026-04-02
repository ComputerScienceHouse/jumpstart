import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()

logger: logging.Logger = logging.getLogger(__name__)


def _get_env_variable(name: str, default: str | None = None) -> str | None:
	"""
	Retrieves an environment variable, with an optional default value.

	Args:
		name (str): The name of the environment variable to retrieve.
		default (str | None): An optional default value to return if the environment variable is not set.

	Returns:
		str | None: The value of the environment variable, or the default value if it is not set.
	"""

	value: str = os.getenv(name, default)

	if value in (None, ""):
		logger.warning(
			f"Environment variable '{name}' is not set, using default value: '{default if default is not None else 'None'}'"
		)
		return default

	return value


BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))

SLACK_API_TOKEN: str | None = _get_env_variable("SLACK_API_TOKEN", None)
SLACK_JUMPSTART_MESSAGE: str = "Would you like to post this message to Jumpstart?"
WATCHED_CHANNELS: tuple[str] = tuple(
	_get_env_variable("WATCHED_CHANNELS", "").split(",")
)
SLACK_DM_TEMPLATE: dict | None = None

CALENDAR_URL: str | None = _get_env_variable("CALENDAR_URL", None)
CALENDAR_OUTLOOK_DAYS: int = int(_get_env_variable("CALENDAR_OUTLOOK_DAYS", "7"))
CALENDAR_EVENT_MAXIMUM: int = int(_get_env_variable("CALENDAR_EVENT_MAXIMUM", "10"))
CALENDAR_TIMEZONE: str = _get_env_variable("CALENDAR_TIMEZONE", "America/New_York")
CALENDAR_CACHE_REFRESH: int = int(_get_env_variable("CALENDAR_CACHE_REFRESH", "10"))

WIKI_API: str | None = _get_env_variable("WIKI_API", None)
WIKIBOT_USER: str | None = _get_env_variable("WIKIBOT_USER", None)
WIKIBOT_PASSWORD: str | None = _get_env_variable("WIKIBOT_PASSWORD", None)
WIKI_CATEGORY: str = _get_env_variable("WIKI_CATEGORY", "JobAdvice")

with open(os.path.join(BASE_DIR, "static", "slack", "dm_request_template.json")) as f:
	SLACK_DM_TEMPLATE = dict(json.load(f))
