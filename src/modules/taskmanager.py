import asyncio

from core import cshcalendar
from logging import getLogger, Logger
from collections.abc import Coroutine

logger: Logger = getLogger(__name__)

running_background_tasks: set[asyncio.Task] = set()

TWENTY_MINUTES = 60 * 20


def handle_task_exception(task: asyncio.Task) -> None:
	"""
	Views ended tasks result, throwing the end error if applicable

	Arguments:
	    Task (asyncio.Task): The task to be
	"""
	try:
		task.result()
	except asyncio.CancelledError:
		logger.info("Background task was cancelled")
	except Exception as e:
		logger.error(f"Background task failed: {e}")

	return


def create_background_task(coroutine: Coroutine) -> asyncio.Task:
	"""
	Creates and executes a background task, holding a strong reference to avoid GC

	Arguments:
	    coroutine (Coroutine): The coroutine object that was created

	Returns:
	    asyncio.Task: The task object that was created and executing
	"""

	task: asyncio.Task = asyncio.create_task(coroutine)
	running_background_tasks.add(task)
	task.add_done_callback(running_background_tasks.discard)
	task.add_done_callback(handle_task_exception)
	return task


async def calendar_worker():
	"""
	Loop to force rebuild the calendar every 20 minutes to check for event updates
	"""
	while True:
		await asyncio.sleep(TWENTY_MINUTES)
		await cshcalendar.rebuild_calendar()
