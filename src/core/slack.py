import re
import copy
import json

from logging import getLogger, Logger

from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.web.slack_response import SlackResponse
from slack_sdk.errors import SlackApiError

from modules import taskmanager

from config import (
	SLACK_API_TOKEN,
	SLACK_JUMPSTART_MESSAGE,
	SLACK_DM_TEMPLATE,
	CALENDAR_TIMEZONE,
	WATCHED_CHANNELS,
)

from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import Request

import asyncio
import httpx

logger: Logger = getLogger(__name__)
client: AsyncWebClient | None = None
event_id_cache: dict[str, str] = {}

EVENT_CACHE_DEBOUNCE = (
	60  # Hold event in for one minute? I think its fine genuiflowkirkenuinelowskinly
)

ACCEPT_MESSAGE: str = "Posting right now :^)"
DENY_MESSAGE: str = (
	"RAHHHHHHHHHHHHHHHHHHHHHHHH HOW DARE YOU :skeleton-shield-banging-here:"
)

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


async def reset_event_from_cache(event_id: str) -> None:
	"""
	Removes an event from the cache

	Arguments:
		event_id (str): The id of the slack event
	"""
	global event_id_cache

	await asyncio.sleep(EVENT_CACHE_DEBOUNCE)
	event_id_cache[event_id] = None
	return


def get_event_retry_amount(event_id: str) -> int:
	"""
	Returns the amount of times a event has been retried

	Arguments:
		event_id (str): The id of the slack event

	Returns:
		int: The amount of times the event has been retried
	"""

	global event_id_cache

	if event_id in event_id_cache:
		event_id_cache[event_id] += 1
		return event_id_cache[event_id]

	event_id_cache[event_id] = 0
	taskmanager.create_background_task(reset_event_from_cache(event_id))
	return event_id_cache[event_id]


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


async def process_slack_events(request: Request) -> dict[str, str]:
	"""
	Processes a slack event, logging and returning the result from the event

	Arguments:
		request (Request): The slack event to be processed

	Returns:
		dict[str, str]: The dictionary to be responded to.
	"""

	try:
		body: dict = await request.json()
		logger.info(f"Received Slack event: {body}")

		event_amounts: int = get_event_retry_amount(body.get("event_id", None))
		if event_amounts > 0:
			logger.info(
				f"SLACK EVENT: Retried event for {body.get('event_id', None)} {event_amounts} time(s)!"
			)
			return ({"status": "success"}, 200)

		# Challenge from Bot Authentication
		if request.headers.get("content-type") == "application/json":
			if body.get("type") == "url_verification":
				logger.info("SLACK EVENT: Was a challenge!")
				return {"challenge": body.get("challenge")}

		event: dict = body.get("event", {})

		if event.get("subtype", None) is not None:
			logger.info("SLACK EVENT: Had a subtype, ignoring it")
			return {"status": "ignored"}

		if event.get("channel", None) not in WATCHED_CHANNELS:
			logger.info(
				"SLACK EVENT: Message was not in a Watched Channel, ignoring it"
			)
			return {"status": "ignored"}

		logger.info("SLACK EVENT: Requesting upload via dm!")
		cleaned_text: str = clean_text(event.get("text", ""))

		taskmanager.create_background_task(
			request_upload_via_dm(event.get("user", ""), cleaned_text)
		)
	except Exception as e:
		logger.error(f"Error handling Slack event: {e}")
		return {"status": "error", "message": str(e)}

	return {"status": "success"}


async def process_slack_message_actions(payload: str):

	try:
		form_json: dict = json.loads(payload)
		response_url = form_json.get("response_url")

		event_amounts: int = get_event_retry_amount(form_json.get("trigger_id", None))
		if event_amounts > 0:
			logger.info(
				f"SLACK MESSAGE ACTION: Retried event for {form_json.get('trigger_id', None)} {event_amounts} time(s)!"
			)
			return {"status": "ignored"}

		if form_json.get("type") != "block_actions":
			return ({}, 200)

		if convert_user_response_to_bool(form_json):
			logger.info(
				"User approved the announcement, Adding it to the announcement list!"
			)

			message_object: dict[str, dict] = json.loads(
				form_json.get("actions", [{}])[0].get("value", '{text:""}')
			).get("text", None)

			user_id = form_json.get("user", {}).get("id")

			username: str = await get_username(user_id)
			username = username[:40] # Only get the first 40 characters so it fits on a single line

			add_announcement(message_object, username)

			if response_url:
				async with httpx.AsyncClient() as client:
					await client.post(
						response_url,
						json={"text": ACCEPT_MESSAGE, "replace_original": True},
					)
		else:
			if response_url:
				async with httpx.AsyncClient() as client:
					await client.post(
						response_url,
						json={"text": DENY_MESSAGE, "replace_original": True},
					)

	except Exception as e:
		logger.error(f"Error in message_actions: {e}")
		return ({"status": "error", "message": str(e)}, 500)

	return ({"status": "success"}, 200)


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
