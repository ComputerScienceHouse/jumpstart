from logging import getLogger, Logger
from datetime import datetime, date, timedelta, time
from zoneinfo import ZoneInfo

# from icalendar import Calendar
from icalendar.cal import Event, Calendar
import httpx
import recurring_ical_events
import arrow

from config import (
	CALENDAR_CACHE_REFRESH,
	CALENDAR_EVENT_MAXIMUM,
	CALENDAR_OUTLOOK_DAYS,
	CALENDAR_TIMEZONE,
	CALENDAR_URL,
)
import asyncio

calendar_cache: tuple[CalendarInfo] = ()  # The current cache of the calendar
cal_last_update: date | None = (
	None  # The last time the calendar was fetched and updated the cache
)
header_none_match: str | None = (
	None  # Used for the httpx.get to see if the current calendar matches
)
header_last_modified: str | None = (
	None  # Used for the httpx.get to see when the calndar was last modified
)
cal_currently_rebuilding: bool = False  # Tells if the calendar is being rebuilt

logger: Logger = getLogger(__name__)
logger.info("Starting up the calendar service!")
cshcal_client = httpx.AsyncClient()


# Automatically format all info into the class
class CalendarInfo:
	"""
	Class that represents standardized calendar info. This is here so when pulling from different things, we can establish it as this class to only update
	certain parts of the codebass
	"""

	def __init__(self, name: str, date_time: date, location: str | None = None):
		self.name: str = name

		if isinstance(date_time, date) and not isinstance(date_time, datetime):
			date_time = date_time.combine(
				date_time, time.min, tzinfo=ZoneInfo(CALENDAR_TIMEZONE)
			)
		elif not date_time.tzinfo:
			date_time = date_time.astimezone(tzinfo=ZoneInfo(CALENDAR_TIMEZONE))
		self.date: arrow.arrow = arrow.get(date_time)  # Arrow has way cooler stuff
		self.location: str | None = location

	def __eq__(self, other):
		if not isinstance(other, CalendarInfo):
			return False
		return (self.name == other.name) and (self.date == other.date)

	def __hash__(self):
		return hash((self.name, self.date))


def format_events(events: tuple[CalendarInfo]) -> dict[str, str]:
	"""
	Formats a parsed list of CalendarInfos, and returns the HTML required for front end

	Args:
		events: The list of CalendarInfos to be formatted

	Returns:
		dict: Returns a dictionary with the "data" key mapping to the HTML data.
	"""

	current_date: date = datetime.now(ZoneInfo(CALENDAR_TIMEZONE))
	final_events: str = "<br>"

	if not events:
		final_events += "<hr style='border: 1px #B0197E solid;'>"
		final_events += (
			"""<div class='calendar-event-container-lvl2'><span class='calendar-text-date'> """
			+ " "
			+ """ </span><br>"""
		)
		final_events += (
			"<span class='calendar-text' id='calendar'>"
			+ "No Events on the Calendar!"
			+ "</span></div>"
		)
		return {"data": final_events}

	for event in events:
		formatted: str = ""
		if event.date < current_date:
			formatted = (
				f"Happening in {event.location}!"
				if event.location
				else "Happening Now!"
			)
		else:
			formatted = event.date.humanize().title()

		final_events += (
			"""<div class='calendar-event-container-lvl2'><span class='calendar-text-date'> """
			+ formatted
			+ """ </span><br>"""
		)
		final_events += (
			"<span class='calendar-text' id='calendar'>"
			+ "".join(event.name)
			+ "</span></div>"
		)
		final_events += "<hr style='border: 1px #B0197E solid;'>"
	return {"data": final_events}


async def rebuild_calendar() -> None:
	"""
	Fetches and rebuilds the global calendar cache. This does NOT return a new cache, but changes the global calendar cache
	"""
	global calendar_cache, cal_last_update, cal_currently_rebuilding

	try:
		found_events: set[CalendarInfo] = set()
		response: httpx.Response = await cshcal_client.get(CALENDAR_URL, timeout=10)
		response.raise_for_status()

		cal: Calendar = Calendar.from_ical(response.content)

		current_time: datetime = datetime.now(ZoneInfo(CALENDAR_TIMEZONE))

		fetched_daily_events: list[Event] = recurring_ical_events.of(cal).between(
			current_time, current_time + timedelta(days=CALENDAR_OUTLOOK_DAYS)
		)

		for event in fetched_daily_events:
			dt = event.get("DTSTART").dt

			if isinstance(dt, date) and not isinstance(dt, datetime):
				dt = datetime.combine(dt, time.min, tzinfo=ZoneInfo(CALENDAR_TIMEZONE))

			elif dt.tzinfo is None:
				dt = dt.replace(tzinfo=ZoneInfo(CALENDAR_TIMEZONE))

			else:
				dt = dt.astimezone(ZoneInfo(CALENDAR_TIMEZONE))

			new_event: CalendarInfo = CalendarInfo(
				event.get("SUMMARY"),
				dt,
				event.get("LOCATION"),
			)

			before = len(found_events)
			found_events.add(new_event)
			after = len(found_events)

			if before == after:
				print("Duplicate detected:", new_event.name, new_event.date)
	except Exception as e:
		logger.warning("Failed to rebuild calendar cache! Error:")
		logger.warning(e)

	cal_last_update = current_time
	calendar_cache = sorted(found_events, key=lambda x: x.date)[
		:CALENDAR_EVENT_MAXIMUM
	]  # Only cache the first elements of this list
	cal_currently_rebuilding = False


async def wait_for_rebuild() -> tuple[CalendarInfo]:
	"""
	Simple yielding function for waiting to return the freshly made calendar cache, rather than proceeding with the obtain

	Returns:
		list: A list of CalendarInfo objects
	"""
	global cal_currently_rebuilding
	while cal_currently_rebuilding:
		await asyncio.sleep(1)

	return calendar_cache


async def get_future_events() -> tuple[CalendarInfo]:
	"""
	Returns the first events up to event maximum within the the calendar outlook day amount
	custom object has name, date and the location

	Returns:
		list: A list of CalendarInfo objects
	"""
	global \
		calendar_cache, \
		cal_last_update, \
		header_last_modified, \
		header_none_match, \
		cal_currently_rebuilding

	if cal_currently_rebuilding:
		return await wait_for_rebuild()

	cur_time: date = datetime.now(ZoneInfo(CALENDAR_TIMEZONE))
	cal_correct_length: bool = len(calendar_cache) == CALENDAR_EVENT_MAXIMUM
	if (
		cal_last_update
		and cal_correct_length
		and (cal_last_update > (cur_time - timedelta(minutes=CALENDAR_CACHE_REFRESH)))
	):
		logger.info("Pulling from CSH calendar cache!")
		return calendar_cache

	cal_currently_rebuilding = True
	logger.info("Checking to rebuild CSH Calendar...")
	try:
		headers: dict[str, str | None] = {}

		if header_none_match:
			headers["If-None-Match"] = header_none_match
		if header_last_modified:
			headers["If-Modified-Since"] = header_last_modified

		response: httpx.Response = await cshcal_client.get(
			CALENDAR_URL, timeout=10, headers=headers
		)
		response.raise_for_status()

		if (  # Nothing changed status code
			response.status_code == 304 and cal_correct_length
		):
			logger.info("CSH calendar not updated, refreshing last update!")
			cal_last_update = cur_time
			return calendar_cache

		header_none_match = response.headers.get("ETag")
		header_last_modified = response.headers.get("Last-Modified")

		if cal_correct_length:
			logger.info("Calendar cache is full length, rebuilding async!")
			asyncio.create_task(
				rebuild_calendar()
			)  # Calendar is correct length, we can just run this in the background
		else:
			logger.info("Calendar cache is NOT full length, yielding rebuild!")
			await rebuild_calendar()

		return calendar_cache
	except Exception as e:
		logger.warning("Failed to fetch the Calendar!")
		logger.warning(e)


async def close_cal_client() -> None:
	"""
	Closes the calendar's HTTPX client, logs if the event loops has been
	closed prior to the function being called
	"""
	global cshcal_client
	try:
		await cshcal_client.aclose()
	except RuntimeError as e:
		logger.warning("EVENT LOOP HAS ALREADY CLOSED, FAILED TO CLOSE csh_cal")
	return
