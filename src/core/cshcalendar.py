from logging import getLogger, Logger
from datetime import datetime
from datetime import date
from datetime import timedelta
from zoneinfo import ZoneInfo
import time

from googleapiclient.discovery import build
from icalendar import Calendar
import requests
import recurring_ical_events
import arrow

import config

logger: Logger = getLogger(__name__)
operation_start_time = time.perf_counter()

logger.info("Starting up the calendar service!")
try:
	calendar_service = build("calendar", "v3", developerKey=config.CALENDAR_API_KEY)
except:
	logger.warning(
		"Failed to build the calendar service, check your API key and internet connection!"
	)


# Automatically format all info into the class
class CalendarInfo:
	"""
	Class that represents standardized calendar info. This is here so when pulling from different things, we can establish it as this class to only update
	certain parts of the codebass
	"""

	def __init__(self, name: str, date_time: date):
		self.name: str = name
		self.date: arrow.arrow = arrow.get(date_time)  # Arrow has way cooler stuff


def report_timing(display_tag: str) -> None:
	"""
	Helper function to report how long an operation took since the lastly established operation start time.

	Args:
	    displayTag: The tag to be printed into the terminal.
	"""

	operation_timestamp = time.perf_counter() - operation_start_time
	logger.info(f"{operation_timestamp}:: {display_tag}")


def format_events(events: list[CalendarInfo]) -> dict:
	"""
	Formats a parsed list of CalendarInfos, and returns the HTML required for front end

	Args:
	    events: The list of CalendarInfos to be formatted

	Returns:
	    dict: Returns a dictionary with the "data" key mapping to the HTML data.
	"""

	current_date: date = datetime.now(ZoneInfo(config.CALENDAR_TIMEZONE))
	final_events = "<br>"

	if not events:
		print("No upcoming events found.")

	for event in events:
		formatted = (
			event.date.humanize() if event.date > current_date else "Happening Now!"
		)
		event.date = formatted
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


def get_future_events_google_api() -> list[CalendarInfo]:
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


def get_future_events_ical() -> list[CalendarInfo]:
	"""
	Fetches the first ten events using the Ical library,
	loops through the first 7 days of the current time.

	    Returns:
	            list: A list of CalendarInfo objects3
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
