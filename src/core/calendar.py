# Use googleapiclient instead, more modern!
# from googleapiclient.discovery import build
from logging import getLogger, Logger
from datetime import datetime
from datetime import timedelta
import time
import requests
import recurring_ical_events
from icalendar import Calendar

from config import CALENDAR_URL
from config import CALENDAR_OUTLOOK_DAYS
from config import CALENDAT_EVENT_MAXIMUM


logger: Logger = getLogger(__name__)
operation_start_time = time.perf_counter()

def report_timing(displayTag : str):
    """
    Helper function for benchmarking calendar speed
	"""
    
    operation_timestamp = time.perf_counter() - operation_start_time
    print(operation_timestamp, "::", displayTag)

def format_events(events : list):
    """
    Formats a parsed list of events and returns the html implementation
    """
    
    return

def get_future_events_ical() -> list:
    """
	Fetches the first ten events using the Ical library.

	Returns:
		list: A list of the events
	"""
    global operation_start_time
    operation_start_time = time.perf_counter() # Set to global operation time for report_timing, this is just here for bunchmarking
    logger.info("Starting Calendar Fetch...")

    found_events = []

    try:
        response = requests.get(CALENDAR_URL)
        report_timing("Fetched the calendar from google")


        cal = Calendar.from_ical(response.content)
        report_timing("Converted the calendar info")
        
        current_day = 1
        current_time = datetime.now()
        returned_events = []

        while (current_day < CALENDAR_OUTLOOK_DAYS) and (len(found_events) < CALENDAT_EVENT_MAXIMUM):
            fetched_daily_events : list = recurring_ical_events.of(cal).between(current_time, current_time + timedelta(days=1))
            report_timing("Sorted events on day " + str(current_day))

            for event in fetched_daily_events:
                if len(found_events) >= CALENDAT_EVENT_MAXIMUM:
                    break
                else:
                    found_events.append(event)

            current_time += timedelta(days=1)
            current_day += 1
    except Exception as e:
        logger.warning("Failed to fetch the Calendar! Failed with error:")
        logger.warning(e)

    sorted_events = sorted(found_events, key=lambda x: x['DTSTART'].dt)
    
    curEvent = 1
    for event in sorted_events:
        print("Event:" + str(curEvent) + "\n\tName: " + event.get("SUMMARY") +  "\n\tDate/Time: " + str(event.get("DTSTART").dt))
        curEvent +=1

    report_timing("FINISHED")
    return returned_events

'''def get_future_events_google():
    now = datetime.now()
    events_result = calendar_service.events().list(
        calendarId='rti648k5hv7j3ae3a3rum8potk@group.calendar.google.com',
        timeMin=now.isoformat(),
        maxResults=10,
        singleEvents=True,
        orderBy='startTime',
    ).execute()
    events = events_result.get('items', [])
    
def calendar():
 # Call the Calendar API
    now = datetime.now()
    events_result = calendar_service.events().list(
        calendarId='rti648k5hv7j3ae3a3rum8potk@group.calendar.google.com',
        timeMin=now.isoformat(),
        maxResults=10,
        singleEvents=True,
        orderBy='startTime',
    ).execute()
    events = events_result.get('items', [])

    final_events = "<br>"

    if not events:
        print('No upcoming events found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        fin_date = parser.parse(start)
        try:
            delta = fin_date - now
        except:
            d = datetime.utcnow()
            delta = fin_date - d
        d
        formatted = format_timedelta(delta) if delta > timedelta(0) else "------"

        final_events += (
            """<div class='calendar-event-container-lvl2'><span class='calendar-text-date'> """
            + formatted +
            """ </span><br>"""
        )
        final_events += (
            "<span class='calendar-text' id='calendar'>"+
            ''.join(event['summary'])+
            "</span></div>"
        )
        final_events += "<hr style='border: 1px #B0197E solid;'>"

    event_list = {'data': final_events}
    return jsonify(event_list)

 '''