# Use googleapiclient instead, more modern!
from googleapiclient.discovery import build

from datetime import datetime
import requests
import recurring_ical_events
from icalendar import Calendar
import logging
'''
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
SERVICE_ACCOUNT_FILE = "path/to/key.json"

creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=SCOPES,
)

service = build("sheets", "v4", credentials=creds)
'''

#rti648k5hv7j3ae3a3rum8potk@group.calendar.google.com
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly'] # The URL to google calender
CALENDAR_URL = "https://calendar.google.com/calendar/embed?src=rti648k5hv7j3ae3a3rum8potk%40group.calendar.google.com&ctz=America%2FNew_York"
calendar_service = build("calendar","v3")

OUTLOOK_DAYS = 7 #The amount of days to go through

def format_events(events : list):
    return

def get_future_events():
    response = requests.get(CALENDAR_URL)
    cal = Calendar.from_ical(response.content)

    
    current_day = datetime.now()
    recurring_ical_events.of(cal).between(datetime.now())
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

 