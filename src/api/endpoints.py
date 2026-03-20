from logging import getLogger, Logger

import json
import httpx
import random
import textwrap

from fastapi import APIRouter, Request, Form
from fastapi.responses import JSONResponse

from core import slack, wikithoughts, cshcalendar
from config import WATCHED_CHANNELS

logger: Logger = getLogger(__name__)
router: APIRouter = APIRouter()


@router.get("/api/calendar")
async def get_calendar() -> JSONResponse:
	"""
	Returns calendar data.

	Returns:
		JSONResponse: A JSON response containing the calendar data.
	"""

	get_future_events_ical: tuple[
		cshcalendar.CalendarInfo
	] = await cshcalendar.get_future_events()
	formatted_events: dict = cshcalendar.format_events(get_future_events_ical)

	return JSONResponse(formatted_events)


@router.get("/api/announcement")
def get_announcement() -> JSONResponse:
	"""
	Returns announcement data.

	Returns:
		JSONResponse: A JSON response containing the announcement data.
	"""

	return JSONResponse({"data": slack.get_announcement()})


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
		logger.info("Received Slack event!")

		body: dict = await request.json()

		if request.headers.get("content-type") == "application/json":
			if body.get("type") == "url_verification":
				return JSONResponse({"challenge": body.get("challenge")})

		if not body:
			return JSONResponse({"challenge": body.get("challenge")})

		event: dict = body.get("event", {})
		cleaned_text: str = slack.clean_text(event.get("text", ""))

		if event.get("subtype", None) is not None:
			return JSONResponse({"status": "ignored"})

		if event not in WATCHED_CHANNELS:
			return JSONResponse({"status": "ignored"})

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
			logger.info("User approved the announcement!")
			logger.info(f"{form_json}\n\n")
			message_object: dict[str, dict] = json.loads(
				form_json.get("actions", [{}])[0].get("value", '{text:""}')
			).get("text", None)
			logger.info(f"Display Object {message_object}")
			slack.add_announcement(message_object)

			if response_url:
				await httpx.post(
					response_url,
					json={"text": "Posting right now :^)", "replace_original": True},
				)
		else:
			if response_url:
				await httpx.post(
					response_url,
					json={"text": "Okay :( maybe next time", "replace_original": True},
				)

	except Exception as e:
		logger.error(f"Error in message_actions: {e}")
		return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

	return JSONResponse({"status": "success"}, status_code=200)


@router.get("/api/wikithought")
async def wikithought() -> JSONResponse:
	"""
	Returns a random CSH wiki thought from the MediaWiki API.

	Returns:
		JSONResponse: A JSON response containing a random Wiki thought.
	"""
	returned_page_data: dict[str, str] = await wikithoughts.get_next_display()
	return JSONResponse(returned_page_data)
