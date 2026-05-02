from logging import getLogger, Logger

from fastapi import APIRouter, Request, Form
from fastapi.responses import JSONResponse

from core import slack, wikithoughts, cshcalendar

logger: Logger = getLogger(__name__)
router: APIRouter = APIRouter()


@router.get("/calendar")
async def get_calendar() -> JSONResponse:
	"""
	Returns calendar data.

	Returns:
		JSONResponse: A JSON response containing the calendar data.
	"""

	events: list[dict[str, str]] = []

	try:
		get_future_events_ical: list[
			cshcalendar.CalendarInfo
		] = await cshcalendar.get_future_events()
		events = cshcalendar.format_events(get_future_events_ical)
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

	return JSONResponse(slack.process_slack_events(request))


@router.post("/slack/message_actions")
async def message_actions(payload: str = Form(...)) -> JSONResponse:
	"""
	Handles slack message action.

	Args:
		payload (str): The payload from the Slack message action.

	Returns:
		JSONResponse: A JSON response indicating the result of the action.
	"""

	response_dict, status_code = slack.process_slack_message_actions(payload)
	return JSONResponse(response_dict, status_code=status_code)


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
