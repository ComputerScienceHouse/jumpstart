import re
import copy
import json

from logging import getLogger, Logger

from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.web.slack_response import SlackResponse
from slack_sdk.errors import SlackApiError

from config import (
	SLACK_API_TOKEN,
	SLACK_JUMPSTART_MESSAGE,
	SLACK_DM_TEMPLATE,
	CALENDAR_TIMEZONE,
)
from datetime import datetime
from zoneinfo import ZoneInfo

logger: Logger = getLogger(__name__)


client: AsyncWebClient | None = None

try:
	client = AsyncWebClient(token=SLACK_API_TOKEN)
except Exception as e:
	logger.error(f"Failed to initialize Slack client: {e}")

current_announcement: dict[str, str] = {
	"content": "Welcome to Jumpstart!",
	"user": "Jumpstart",
	"timestamp": datetime.now(ZoneInfo(CALENDAR_TIMEZONE))
	.strftime("%I:%M %p")
	.lstrip("0"),
}


def clean_text(raw: str) -> str:
	"""
	Strip Slack mrkdwn, HTML entities, and formatting characters.

	Args:
		raw (str): The raw text to be cleaned.

	Returns:
		str: The cleaned text.
	"""

	text: str = re.sub(r"<[^>]+>", "", str(raw), flags=re.IGNORECASE)
	text = re.sub(r"&lt;.*?&gt;", "", text, flags=re.IGNORECASE)
	return text.replace("*", "").replace("_", "").replace("`", "").strip()


async def gather_emojis() -> dict:
	"""
	Gathers emojis from Slack and returns a mapping of emoji names to their URLs.

	Returns:
		dict: A mapping of emoji names to their URLs.
	"""

	emojis: dict = {}

	try:
		if client is None:
			raise ValueError("Slack client is not initialized")

		emoji_request: dict = await client.emoji_list()
		assert emoji_request.get("ok", False)

		emojis = emoji_request.get("emoji", {})
	except Exception as e:
		logger.error(f"Error gathering emojis: {e}")

	return emojis


async def get_username(user_id: str) -> str:
	"""
	Attempts to retrieve a slack username relating to a user id

	Args:
		user_id (str): The ID of the user to retrieve

	Returns:
		str: The username, or an empty string if not applicable
	"""

	response = await client.users_info(user=user_id)
	user = response.get("user", None)

	if user is None:
		logger.warning(f"Unable to find a user under the id {user_id}")
		return "Unknown"

	display_name = user.get("profile", {}).get("display_name", None)
	real_name = user.get("real_name", None)
	username = user.get("name", None)

	return real_name or display_name or username or "Unknown"


async def request_upload_via_dm(user_id: str, announcement_text: str) -> None:
	"""
	Sends a DM to the user with the announcement text and a prompt to post it to Jumpstart.

	Args:
		user_id (str): The ID of the user to send the DM to.
		announcement_text (str): The text of the announcement to be posted.
	"""

	try:
		if client is None:
			raise ValueError("Slack client is not initialized")

		message: dict = copy.deepcopy(SLACK_DM_TEMPLATE)

		message[0]["text"]["text"] += announcement_text
		message[1]["elements"][0]["value"] = json.dumps(
			{
				"text": announcement_text,
				"user": user_id,
			}
		)

		await client.chat_postMessage(
			channel=user_id, text=SLACK_JUMPSTART_MESSAGE, blocks=message
		)
	except SlackApiError as e:
		logger.error(f"Slack Error: {e.response['error']}\n")
		logger.error(f"Full Slack Error: {e.response}")
	except Exception as e:
		logger.error(f"Error messaging user {user_id}: {e}")


def convert_user_response_to_bool(message_data: dict) -> bool:
	"""
	Converts a Slack message action response to a boolean indicating whether the user approved the announcement.

	Args:
		message_data (dict): The data from the Slack message action payload.

	Returns:
		bool: True if the user approved the announcement, False otherwise.
	"""

	user_response: bool = False

	try:
		user_response = (
			message_data.get("actions", [{}])[0].get("action_id", "no_j") == "yes_j"
		)
	except Exception as e:
		logger.error(f"Failed to parse data: {e}")

	return user_response


def get_announcement() -> dict[str, str] | None:
	"""
	Returns the next announcement in the queue.

	Returns:
		dict[str,str]: The next announcement text and user, or None if there are no announcements.
	"""

	return current_announcement


def add_announcement(announcement_text: str, username: str) -> None:
	"""
	Adds an announcement to the queue.

	Args:
		announcement_text (str): The text of the announcement to be added.
		user_id (str): The user_id of the person
	"""
	global current_announcement

	if announcement_text is None or announcement_text.strip() == "":
		logger.warning("Attempted to add empty announcement, skipping!")
		return

	current_time = (
		datetime.now(tz=ZoneInfo(CALENDAR_TIMEZONE)).strftime("%I:%M %p").lstrip("0")
	)
	new_addition: dict[str, str] = {
		"content": announcement_text,
		"user": username,
		"timestamp": current_time,
	}

	current_announcement = new_addition
