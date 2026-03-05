# Use googleapiclient instead, more modern!
# from googleapiclient.discovery import build
from logging import getLogger, Logger
import datetime
import time
import requests
import recurring_ical_events
import arrow
from icalendar import Calendar
from zoneinfo import ZoneInfo

from config import CALENDAR_URL
from config import CALENDAR_OUTLOOK_DAYS
from config import CALENDAR_EVENT_MAXIMUM
from config import CALENDAR_TIMEZONE

logger: Logger = getLogger(__name__)
operation_start_time = time.perf_counter()

# Automatically format all info into the 
class CalendarInfo:
    def __init__(self,name : str,date : datetime.date):
        self.Name : str = name
        self.Date : arrow.arrow = arrow.get(date) # Arrow has way cooler stuff

def report_timing(displayTag : str) -> None:
    """
    Helper function to report how long an operation took since the lastly established operation start time.

    Args:
        displayTag: The tag to be printed into the terminal.
    """
    
    operation_timestamp = time.perf_counter() - operation_start_time
    logger.info(operation_timestamp, "::", displayTag)

def format_events(events : list[CalendarInfo]) -> dict:
    """
    Formats a parsed list of CalendarInfos, and returns the HTML required for front end

    Args:
        events: The list of CalendarInfos to be formatted

    Returns:
        dict: Returns a dictionary with the "data" key mapping to the HTML data.
    """

    currentDate : datetime.date = datetime.datetime.now(ZoneInfo(CALENDAR_TIMEZONE))
    final_events = "<br>"

    if not events:
        print('No upcoming events found.')

    for event in events:
        formatted = event.Date.humanize(['year']) if event.Date > currentDate else "Happening Now!"
        event.Date = formatted
        final_events += (
            """<div class='calendar-event-container-lvl2'><span class='calendar-text-date'> """
            + formatted +
            """ </span><br>"""
        )
        final_events += (
            "<span class='calendar-text' id='calendar'>"+
            ''.join(event.Name)+
            "</span></div>"
        )
        final_events += "<hr style='border: 1px #B0197E solid;'>"
    return {"data": final_events}

def get_future_events_ical() -> list[CalendarInfo]:
    """
	Fetches the first ten events using the Ical library, loops through the first 7 days of the current time.

	Returns:
		list: A list of CalendarInfo objects
	"""
    global operation_start_time
    operation_start_time = time.perf_counter() # Set to global operation time for report_timing, this is just here for bunchmarking
    logger.info("Starting Calendar Fetch...")

    found_events :list[CalendarInfo] = []

    try:
        response = requests.get(CALENDAR_URL)
        report_timing("Fetched the calendar from google")


        cal = Calendar.from_ical(response.content)
        report_timing("Converted the calendar info")
        
        current_day = 1
        current_time = datetime.datetime.now(ZoneInfo(CALENDAR_TIMEZONE))

        while (current_day < CALENDAR_OUTLOOK_DAYS) and (len(found_events) < CALENDAR_EVENT_MAXIMUM):
            fetched_daily_events : list = recurring_ical_events.of(cal).between(current_time, current_time + datetime.timedelta(days=1))
            report_timing("Sorted events on day " + str(current_day))

            for event in fetched_daily_events:
                if len(found_events) >= CALENDAR_EVENT_MAXIMUM:
                    break
                else:
                    newEvent = CalendarInfo(event.get("SUMMARY"), event.get("DTSTART").dt)
                    found_events.append(newEvent)

            current_time += datetime.timedelta(days=1)
            current_day += 1
    except Exception as e:
        logger.warning("Failed to fetch the Calendar! Failed with error:")
        logger.warning(e)

    sorted_events = sorted(found_events, key=lambda x: x.Date)
    return sorted_events
