from logging import getLogger, Logger

import json
import httpx
import random
import textwrap

from fastapi import APIRouter, Request, Form
from fastapi.responses import JSONResponse

from core import slack, cshcalendar, wikithoughts

logger: Logger = getLogger(__name__)
router: APIRouter = APIRouter()


@router.get("/calendar")
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


@router.get("/announcement")
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

		if not event.get("channel", "") in slack.WATCHED_CHANNELS:
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

			slack.add_announcement(form_json.get("text", None))

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


@router.get("/wikithought")
async def wikithought() -> JSONResponse:
	returned_page_data: dict[str, str] = await wikithoughts.get_next_display()
	return JSONResponse(returned_page_data)


@router.get("/showerthoughts")
async def showerthoughts() -> JSONResponse:
	"""
	Returns a random shower thought from the Reddit API.

	Returns:
		JSONResponse: A JSON response containing a random shower thought.
	"""

	response: dict = {"data": "No shower thoughts found."}

	try:
		logger.info("Fetching shower thoughts from Reddit API...")

		async with httpx.AsyncClient() as client:
			reddit_data: httpx.Response = await client.get(
				"https://www.reddit.com/r/showerthoughts/top.json",
				headers={"User-agent": "Showerthoughtbot 0.1"},
			)

			reddit_json = reddit_data.json()

		if len(reddit_json["data"]["children"]) == 0:
			logger.warning("No shower thoughts found in Reddit API response.")
			return JSONResponse(response)

		shower_thought: str = textwrap.fill(
			(random.choice(reddit_json["data"]["children"])["data"]["title"]), 50
		)

		response["data"] = shower_thought
	except Exception as e:
		logger.error(f"Error fetching shower thoughts: {e}")

	return JSONResponse(response)
