import json
from logging import Logger, getLogger

import httpx
from fastapi import APIRouter, Form, Request
from fastapi.responses import JSONResponse

from config import WATCHED_CHANNELS
from core import cshcalendar, slack, wikithoughts

logger: Logger = getLogger(__name__)
router: APIRouter = APIRouter()

ACCEPT_MESSAGE: str = "Posting right now :^)"
DENY_MESSAGE: str = "Okay :( maybe next time"


@router.get("/calendar")
async def get_calendar() -> JSONResponse:
	"""
	Returns calendar data.

	Returns:
		JSONResponse: A JSON response containing the calendar data.
	"""

	events: list[dict[str, str]] = []

	try:
		get_future_events_ical: (
			list[cshcalendar.CalendarInfo] | None
		) = await cshcalendar.get_future_events()

		if get_future_events_ical is None:
			raise Exception("Gathering future events resulted in None")

		events.extend(cshcalendar.format_events(get_future_events_ical))
	except Exception as e:
		logger.error(f"Error fetching calendar events: {e}")
		return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

	return JSONResponse({"data": events})


@router.get("/announcement")
def get_announcement() -> JSONResponse:
	"""
	Returns announcement data.

	Returns:
		JSONResponse: A JSON response containing the announcement data.
	"""

	return JSONResponse(slack.get_announcement())


@router.post("/slack/events")
async def slack_events(request: Request) -> JSONResponse:
	"""
	Handles slack events.

	Args:
		request (Request): The incoming request from Slack.

	Returns:
		JSONResponse: A JSON response indicating the result of the event handling.
	"""

	try:
		logger.debug(f"Received Slack event: {await request.body()}")

		body: dict = await request.json()

		if request.headers.get("content-type") == "application/json":
			if body.get("type") == "url_verification":
				logger.info("SLACK EVENT: Was a challenge!")
				return JSONResponse({"challenge": body.get("challenge")})

		if not body:
			logger.debug("SLACK EVENT: Was a challenge, with no body")
			return JSONResponse({"challenge": body.get("challenge")})

		event: dict = body.get("event", {})
		cleaned_text: str = slack.clean_text(event.get("text", ""))

		if event.get("subtype", None) is not None:
			logger.info("SLACK EVENT: Had no subtype, ignoring it")
			return JSONResponse({"status": "ignored"})

		if event.get("channel", None) not in WATCHED_CHANNELS:
			logger.info(
				"SLACK EVENT: Message was not in a Watched Channel, ignoring it"
			)
			return JSONResponse({"status": "ignored"})

		logger.info("SLACK EVENT: Requesting upload via dm!")
		await slack.request_upload_via_dm(event.get("user", ""), cleaned_text)
	except Exception as e:
		logger.error(f"Error handling Slack event: {e}")
		return JSONResponse({"status": "error", "message": str(e)})

	return JSONResponse({"status": "success"})


@router.post("/slack/message_actions")
async def message_actions(payload: str = Form(...)) -> JSONResponse:
	"""
	Handles slack message action.

	Args:
		payload (str): The payload from the Slack message action.

	Returns:
		JSONResponse: A JSON response indicating the result of the action.
	"""

	try:
		form_json: dict = json.loads(payload)
		response_url = form_json.get("response_url")

		if form_json.get("type") != "block_actions":
			return JSONResponse({}, status_code=200)

		if slack.convert_user_response_to_bool(form_json):
			logger.info(
				"User approved the announcement, Adding it to the announcement list!"
			)

			message_object: str | None = json.loads(
				form_json.get("actions", [{}])[0].get("value", {})
			).get("text", None)

			user_id = form_json.get("user", {}).get("id")

			username: str = await slack.get_username(user_id=user_id)
			username = username[:40]

			slack.add_announcement(message_object, username)

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
		return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

	return JSONResponse({"status": "success"}, status_code=200)


@router.get("/wikithought")
async def wikithought() -> JSONResponse:
	"""
	Returns a random CSH wiki thought from the MediaWiki API.

	Returns:
		JSONResponse: A JSON response containing a random Wiki thought.
	"""

	page_data: dict | None = None

	try:
		page_data = await wikithoughts.get_next_display()
	except Exception as e:
		logger.error(f"Error fetching wiki thought: {e}")
		return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

	return JSONResponse(page_data)
