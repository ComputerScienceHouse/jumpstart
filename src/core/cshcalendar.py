from logging import getLogger, Logger
from datetime import datetime, date, timedelta, time
from zoneinfo import ZoneInfo

from icalendar.cal import Event, Calendar
import httpx
import recurring_ical_events
import arrow
import re

from config import (
	CALENDAR_CACHE_REFRESH,
	CALENDAR_EVENT_MAXIMUM,
	CALENDAR_OUTLOOK_DAYS,
	CALENDAR_TIMEZONE,
	CALENDAR_URL,
)
import asyncio

calendar_cache: list[CalendarInfo] = []  # The current cache of the calendar
cal_last_update: date | None = (
	None  # The last time the calendar was fetched and updated the cache
)
header_none_match: str | None = (
	None  # Used for the httpx.get to see if the current calendar matches
)
header_last_modified: str | None = (
	None  # Used for the httpx.get to see when the calndar was last modified
)
cal_constructed_event: asyncio.Event = asyncio.Event()
cal_constructed_event.clear()

logger: Logger = getLogger(__name__)
logger.info("Starting up the calendar service!")
cshcal_client = httpx.AsyncClient()

# Conversion from seconds
MINUTE: int = 60
HOUR: int = MINUTE * 60
DAY: int = HOUR * 24
WEEK: int = DAY * 7

"""
This is used for each "check" from the time humanizer. %TIME% will be replaced with a rounded
WARNING: PERCENTAGE SIGNS WILL TRIGGER A REGEX OPERATION
WARNING: FOLLOW INSERTION ORDER
"""
HUMANIZER_CHECKS: dict[int, str] = {
	MINUTE: "In 1 Minute",
	(HOUR - MINUTE): f"In %{MINUTE}% Minutes",
	(HOUR * 1.5): "In 1 Hour",
	(DAY - HOUR): f"In %{HOUR}% Hours",
	(DAY * 1.33): "In 1 Day",
	(WEEK - DAY): f"In %{DAY}% Days",
}

BORDER_STRING: str = '<hr class="calendar-border">'
TIME_PATTERN = re.compile(r"%([^%]+)%")


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
		return (self.name == other.name) and (self.date == other.date)

	def __hash__(self):
		return hash((self.name, self.date))


def ceil_division(num: int, den: int) -> int:
	"""
	Returns a ceiling division of the two numbers
	Args:
		num (int): the numerator
		den (int): the denominator

	Returns:
		int: the result of the operation
	"""

	return (num + den - 1) // den


def time_humanizer(current_time: datetime, event_time: datetime) -> str:
	"""
	Custom humanizer for text to be displayed

	Args:
		current_time (datetime): The current time to be judged off of
		event_time (datetime): The events time to be factored
	Returns:
		str: The humanized time as a string
	"""

	def repl(match: re.Match[str]) -> str:
		"""
		Replaces the matched group text

		Args:
			match (re.Match[str]): The matches group

		Returns:
			str: The newly formatted string
		"""

		num = int(match.group(1))
		return str(round(time_before_event / num))

	time_before_event: int = (event_time - current_time).total_seconds()

	if time_before_event > WEEK:
		return "Over a Week Away"

	unformatted_string: str = (
		"------"  # Make this the default, incase an operation fails
	)

	for key in HUMANIZER_CHECKS.keys():
		if time_before_event < key:
			unformatted_string = HUMANIZER_CHECKS.get(
				key, "Unable to find appropriate humanizer text"
			)
			break

	return TIME_PATTERN.sub(repl, unformatted_string)


def calendar_to_html(seg_header: str, seg_content: str) -> str:
	"""
	Formats a header and content into the HTML for the calendar front end

	Args:
		seg_header (str): The header of the calendar segment
		seg_content (str): The content in the calendar segment

	Returns:
		str:
	"""

	ret_string: str = (
		"""<div class='calendar-event-container-lvl2'><span class='calendar-text-date'> """
		+ seg_header
		+ """ </span><br>"""
	)
	ret_string += (
		"<span class='calendar-text' id='calendar'>" + seg_content + "</span></div>"
	)
	return ret_string


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
		final_events += BORDER_STRING

		final_events += calendar_to_html(":(", "No Events on the Calendar")

		final_events += BORDER_STRING

		return {"data": final_events}

	for event in events:
		event_cur_happening: bool = event.date < current_date
		if event_cur_happening:
			formatted: str = (
				f"Happening in {event.location}!"
				if event.location
				else "Happening Now!"
			)
			final_events += calendar_to_html(formatted, event.name)
		else:
			final_events += calendar_to_html(
				time_humanizer(current_date, event.date), event.name
			)

		final_events += BORDER_STRING
	return {"data": final_events}


async def rebuild_calendar() -> None:
	"""
	Fetches and rebuilds the global calendar cache. This does NOT return a new cache, but changes the global calendar cache
	"""

	global calendar_cache, cal_last_update, cal_constructed_event

	current_time: datetime = datetime.now(ZoneInfo(CALENDAR_TIMEZONE))
	try:
		cal_constructed_event.clear()
		found_events: set[CalendarInfo] = set()
		response: httpx.Response = await cshcal_client.get(CALENDAR_URL, timeout=10)
		response.raise_for_status()

		cal: Calendar = Calendar.from_ical(response.content)

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

			found_events.add(new_event)

		cal = None
		fetched_daily_events = None
	except Exception as e:
		logger.warning("Failed to rebuild calendar cache! Error:")
		logger.warning(e)
		cal_constructed_event.set()

	cal_last_update = current_time
	calendar_cache = sorted(found_events, key=lambda x: x.date)[
		:CALENDAR_EVENT_MAXIMUM
	]  # Only cache the first elements of this list
	cal_constructed_event.set()


async def get_future_events() -> list[CalendarInfo]:
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
		cal_constructed_event

	if not cal_constructed_event.is_set():
		await cal_constructed_event.wait()
		return calendar_cache

	cur_time: date = datetime.now(ZoneInfo(CALENDAR_TIMEZONE))
	cal_correct_length: bool = len(calendar_cache) == CALENDAR_EVENT_MAXIMUM

	if (
		cal_last_update
		and cal_correct_length
		and (cal_last_update > (cur_time - timedelta(minutes=CALENDAR_CACHE_REFRESH)))
	):
		logger.info("Pulling from CSH calendar cache!")
		return calendar_cache

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

		if (
			not cal_constructed_event.is_set()
		):  # Double check, since it might have changed for the last modifed
			await cal_constructed_event.wait()
			return calendar_cache

		if cal_correct_length:
			logger.info("Calendar cache is full length, rebuilding async!")
			async with asyncio.TaskGroup() as taskGroup:
				taskGroup.create_task(rebuild_calendar())
				# Calendar is correct length, we can just run this in the background
		else:
			logger.info("Calendar cache is NOT full length, yielding rebuild!")
			await rebuild_calendar()

		return calendar_cache
	except Exception as e:
		logger.warning("Failed to fetch the Calendar!")
		logger.warning(e)


async def close_client() -> None:
	"""
	Closes the calendar's HTTPX client, logs if the event loops has been
	closed prior to the function being called
	"""

	global cshcal_client
	try:
		await cshcal_client.aclose()
		logger.info("Succesfully closed the cshcal client")
	except RuntimeError:
		logger.warning("EVENT LOOP HAS ALREADY CLOSED, FAILED TO CLOSE csh_cal")
