from logging import getLogger, Logger

from slack_sdk.web.async_client import AsyncWebClient

from modules import taskmanager
from core import slack

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import asyncio

from typing import Any
from config import (
	CALENDAR_TIMEZONE,
	SLACK_ACTIVE_GROUP_ID,
	SLACK_FROSH_GROUP_ID,
	SLACK_MEETINGS_GROUP_ID,
	SLACK_TEST_GROUP_ID,
)

logger: Logger = getLogger(__name__)
client: AsyncWebClient | None = None

event_id_cache: dict[str, str] = {}
queued_announcement_id_cache: dict[str, Any] = {}

TEN_MINUTES = 60 * 10
TECHNICAL_SEMINAR_KEYWORD: str = "technical"
STANDARD_SEMINAR_KEYWORD: str = "seminar"
MEETING_KEYWORD: str = "meeting"
TEST_KEYWORD: str = "test_gick"

MINUTES_BEFORE_EVENT_PING = 15

async def create_announcement_worker(
	event_uid: str, event_recurrence_id: str, text: str, event_time: datetime
) -> None:
	"""
	Creates a new worker that will send an announcement 15 minutes before the stated event

	Args:
		event_uid (str): The UID for the recurring event
		event_recurrence_id (str): The ID for which occuring event it is.
		text (str): The message to be sent
		event_time (datetime): The time for the event.
	"""
	key: str = f"{event_uid}:{event_recurrence_id}"  # we should use redis instead

	if key in queued_announcement_id_cache:
		return


	current_time: datetime = datetime.now(ZoneInfo(CALENDAR_TIMEZONE))
	logger.info(text)

	if current_time < (event_time + timedelta(minutes=MINUTES_BEFORE_EVENT_PING)):
		wait_time = event_time - current_time + timedelta(minutes=MINUTES_BEFORE_EVENT_PING)
		try:
			task = asyncio.create_task(asyncio.sleep(wait_time.total_seconds()))
			queued_announcement_id_cache[key] = task
			await task
		finally:
			queued_announcement_id_cache.pop(key, None)

		await slack.send_announcement_message(text)
		await asyncio.sleep(TEN_MINUTES)



def check_for_announcement(event: dict[str, Any], time: datetime) -> None:
	"""
	Checks to see if a worker needs to be created for an event

	Args:
		event (dict[str, str]): The information for the event
		time (datetime): The time for the event
	"""
	description: str = event.get("DESCRIPTION", "")
	if not description:
		return

	title: str = event.get("SUMMARY", "")
	if not title:
		return

	uid: str = str(event.get("UID", ""))
	if not uid:
		return

	recurrence_id = event.get("RECURRENCE-ID", None)
	if not recurrence_id:
		return

	rec_id: str = recurrence_id.dt.isoformat()

	description = description.lower().strip()
	if TEST_KEYWORD.lower() in description:
		taskmanager.create_background_task(
			create_announcement_worker(
				uid, rec_id, f"<!subteam^{SLACK_TEST_GROUP_ID}> testing!", time
			)
		)

	# if TECHNICAL_SEMINAR_KEYWORD.lower() in description:
	# 	taskmanager.create_background_task(create_announcement_worker(
	# 		uid, rec_id, f"<!subteam^{SLACK_ACTIVE_GROUP_ID}> reminder: meeting starting soon", time
	# 	))
