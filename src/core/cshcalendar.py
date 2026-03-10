from logging import getLogger, Logger
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from icalendar import Calendar

import time
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
cal_last_update: date = (
	None  # The last time the calendar was fetched and updated the cache
)
header_none_match: str = (
	None  # Used for the httpx.get to see if the current calendar matches
)
header_last_modified: str = (
	None  # Used for the httpx.get to see when the calndar was last modified
)
cal_currently_rebuilding: bool = False  # Tells if the calendar is being rebuilt

logger: Logger = getLogger(__name__)
operation_start_time: float = time.perf_counter()
logger.info("Starting up the calendar service!")

client = httpx.AsyncClient()

"""try:
	calendar_service = build("calendar", "v3", developerKey=config.CALENDAR_API_KEY)
except:
	logger.warning(
		"Failed to build the calendar service, check your API key and internet connection!"
	)

"""


# Automatically format all info into the class
class CalendarInfo:
	"""
	Class that represents standardized calendar info. This is here so when pulling from different things, we can establish it as this class to only update
	certain parts of the codebass
	"""

	def __init__(self, name: str, date_time: date, location: str | None = None):
		self.name: str = name
		self.date: arrow.arrow = arrow.get(date_time)  # Arrow has way cooler stuff
		self.location: str | None = location

	def __eq__(self, other):
		if not isinstance(other, CalendarInfo):
			return False
		return self.name == other.name

	def __hash__(self):
		return hash(
			self.name
		)  # Might be stupid only hashing off name, but as of right now I think the implementation works


def report_timing(display_tag: str) -> None:
	"""
	Helper function to report how long an operation took since the lastly established operation start time.

	Args:
	    displayTag: The tag to be printed into the terminal.
	"""

	operation_timestamp = time.perf_counter() - operation_start_time
	logger.info(f"{operation_timestamp}:: {display_tag}")


def format_events(events: tuple[CalendarInfo]) -> dict:
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
			formatted = event.date.humanize()
			formatted = formatted.title()

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


async def rebuild_calendar():
	"""
	Fetches and rebuilds the global calendar cache. This does NOT return a new cache, but changes the global calendar cache
	"""
	global calendar_cache, cal_last_update

	found_events: set[CalendarInfo] = set()
	try:
		response = await client.get(CALENDAR_URL, timeout=10)
		response.raise_for_status()
		report_timing("Fetched the calendar from google")

		cal = Calendar.from_ical(response.content)
		report_timing("Converted the calendar info")

		current_time = datetime.now(ZoneInfo(CALENDAR_TIMEZONE))

		fetched_daily_events: list = recurring_ical_events.of(cal).between(
			current_time, current_time + timedelta(days=CALENDAR_OUTLOOK_DAYS)
		)

		for event in fetched_daily_events:
			if len(found_events) >= CALENDAR_EVENT_MAXIMUM:
				break

			new_event = CalendarInfo(
				event.get("SUMMARY"),
				event.get("DTSTART").dt,
				event.get("LOCATION"),
			)
			found_events.add(new_event)
	except Exception as e:
		logger.warning("Failed to rebuild calendar cache! Error:")
		logger.warning(e)

	cal_last_update = datetime.now()
	calendar_cache = sorted(found_events, key=lambda x: x.date)


async def wait_for_rebuild():
	"""
	Simple yielding function for waiting to return the freshly made calendar cache, rather than proceeding with the obtain

	    Returns:
	        list: A list of CalendarInfo objects
	"""
	global cal_currently_rebuilding
	while cal_currently_rebuilding:
		asyncio.sleep(1)

	return calendar_cache


async def get_future_events():
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

	cal_correct_length = len(calendar_cache) == CALENDAR_EVENT_MAXIMUM
	if (
		cal_last_update
		and cal_correct_length
		and cal_last_update
		> (datetime.now() - timedelta(minutes=CALENDAR_CACHE_REFRESH))
	):
		logger.info("Pulling from CSH calendar cache!")
		return calendar_cache

	logger.info("Checking to rebuild CSH Calendar...")
	try:
		headers = {}
		if header_none_match:
			headers["If-None-Match"] = header_none_match
		if header_last_modified:
			headers["If-Modified-Since"] = header_last_modified

		response = await client.get(CALENDAR_URL, timeout=10, headers=headers)
		response.raise_for_status()

		if (  # Nothing changed status code
			response.status_code == 304 and cal_correct_length
		):
			logger.info("CSH calendar not updated, refreshing last update!")
			cal_last_update = datetime.now()
			return calendar_cache

		header_none_match = response.headers.get("ETag")
		header_last_modified = response.headers.get("Last-Modified")

		if cal_currently_rebuilding:
			return await wait_for_rebuild()

		if cal_correct_length:
			logger.info("Calendar cache is full length, rebuilding async!")
			asyncio.create_task(
				rebuild_calendar()
			)  # Calendar is correct length, we can just run this in the background
		else:
			logger.info("Calendar cache is NOT full length, yielding rebuild!")
			cal_currently_rebuilding = True
			await rebuild_calendar()
			cal_currently_rebuilding = False
		return calendar_cache
	except Exception as e:
		logger.warning("Failed to fetch the Calendar!")
		logger.warning(e)


def close_client():
	global client
	client.aclose()


'''def get_future_events_ical() -> list[CalendarInfo]:
	"""
	Fetches the first ten events using the Ical library,
	loops through the first 7 days of the current time.

	    Returns:
	        list: A list of CalendarInfo objects
	"""
	found_events: list[CalendarInfo] = []
	try:
		response = requests.get(config.CALENDAR_URL, timeout=10)
		report_timing("Fetched the calendar from google")

		cal = Calendar.from_ical(response.content)
		report_timing("Converted the calendar info")

		current_day = 1
		current_time = datetime.now(ZoneInfo(config.CALENDAR_TIMEZONE))

		while (current_day < config.CALENDAR_OUTLOOK_DAYS) and (
			len(found_events) < config.CALENDAR_EVENT_MAXIMUM
		):
			fetched_daily_events: list = recurring_ical_events.of(cal).between(
				current_time, current_time + timedelta(days=1)
			)
			report_timing("Sorted events on day " + str(current_day))

			for event in fetched_daily_events:
				if len(found_events) >= config.CALENDAR_EVENT_MAXIMUM:
					break
				else:
					new_event = CalendarInfo(
						event.get("SUMMARY"), event.get("DTSTART").dt
					)
					found_events.append(new_event)

			current_time += timedelta(days=1)
			current_day += 1
	except Exception as e:
		logger.warning("Failed to fetch the Calendar! Failed with error:")
		logger.warning(e)

	sorted_events = sorted(found_events, key=lambda x: x.date)
	return sorted_events
'''

'''def get_future_events_google_api() -> list[CalendarInfo]:
	"""
	    Fetches the first ten events using the google api client.
	Requires an API key to be estbalished as a env variable

	    Returns:
	            list: A list of CalendarInfo objects3
	"""
	# pylint: disable=no-member
	events_result = (
		calendar_service.events()
		.list(
			calendarId="rti648k5hv7j3ae3a3rum8potk@group.calendar.google.com",
			timeMin=datetime.now(ZoneInfo(config.CALENDAR_TIMEZONE)).isoformat(),
			maxResults=10,
			singleEvents=True,
			orderBy="startTime",
		)
		.execute()
	)

	events = events_result.get("items", [])
	formatted_events: list[CalendarInfo] = []

	for event in events:
		start = event["start"].get("dateTime") or event["start"].get("date")
		new_event = CalendarInfo(event["summary"], datetime.fromisoformat(start))
		formatted_events.append(new_event)

	return formatted_events
'''
