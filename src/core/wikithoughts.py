import httpx
import asyncio
from datetime import datetime, timedelta
from itertools import islice
from typing import Pattern
from config import WIKIBOT_PASSWORD, WIKIBOT_USER, WIKI_CATEGORY, WIKI_API
import logging
import random
import re

CYCLE_DEBOUNCE_TIME: int = 12  # How long it takes to resfresh wiki titles
BATCH_SIZE: int = 50  # max titles per request
REAUTHENTICATE_ATTEMPTS: int = (
	3  # The amount of times it will attempt to re-authenticare
)

HEADERS: dict[str, str] = {"User-Agent": "JumpstartFetcher/1.0"}
AUTH: tuple[str] = (WIKIBOT_USER, WIKIBOT_PASSWORD)

client: httpx.AsyncClient = httpx.AsyncClient(headers=HEADERS, auth=AUTH)

logger: logging.Logger = logging.getLogger(__name__)

bot_authenticated: bool = False
last_updated_time: datetime | None = None

page_title_cache: list = []
page_dict_cache: dict = {}

etag: str | None = None
last_modifed: str | None = None

queued_pages: list[str] = []
shown_pages: list[str] = []
current_page: dict[str, str] = {"page": "NA", "content": "NA"}

page_last_updated: datetime | None = None


# Precompile all the Regex operations
RE_LINK: Pattern[str] = re.compile(r'\[https?://[^\s"]+\s+"?([^\]"]+)"?\]')
RE_FILE: Pattern[str] = re.compile(r"\[\[File:[^\]]*\]\]", re.IGNORECASE)
RE_IMAGE: Pattern[str] = re.compile(r"\[\[Image:[^\]]*\]\]", re.IGNORECASE)
RE_PAGE_TEXT: Pattern[str] = re.compile(r"\[\[[^\|\]]*\|([^\]]+)\]\]")
RE_PAGE: Pattern[str] = re.compile(r"\[\[([^\]]+)\]\]")
RE_CSH: Pattern[str] = re.compile(r"\^\^([^^]+)\^\^")
RE_TEMPLATE: Pattern[str] = re.compile(r"\{\{.*?\}\}", re.DOTALL)
RE_HTML: Pattern[str] = re.compile(r"<[^>]+>")
RE_BOLD_ITALIC: Pattern[str] = re.compile(r"''+")


def clean_wikitext(text: str) -> str:
	"""
	Function for cleaning markdown text using regex commands

	Args:
		text (str): The text to be cleaned

	Returns:
		str: The cleaned up text string
	"""

	reg_operations: tuple[Pattern[str]] = (
		RE_LINK,
		RE_FILE,
		RE_IMAGE,
		RE_PAGE_TEXT,
		RE_PAGE,
		RE_CSH,
		RE_TEMPLATE,
		RE_HTML,
		RE_BOLD_ITALIC,
	)

	for operation in reg_operations:
		swap_text: str = ""
		if operation in (
			RE_LINK,
			RE_PAGE,
			RE_PAGE_TEXT,
		):  # Keep text inbetween the anchors
			swap_text = r"\1"
		elif operation == (RE_CSH):  # Add user infront of the CSH user
			swap_text = r"User \1"

		text = operation.sub(swap_text, text)

	return text.strip()


def batch_iterable(iterable: list, size: int):
	"""
	Generator function for splitting up lists into smaller lists
	To be frank, found this online when researching about the MediaWiki API

	Args:
		iterable (list): The iterable to be split up for batches
		size (int): the size of the batches
	Yields:
	    A batch split by the requested size
	"""
	it = iter(iterable)
	while True:
		batch = list(islice(it, size))
		if not batch:
			break
		yield batch


async def auth_bot() -> None:
	"""
	Authenticates the CSH Wiki bot, logging if it was successful or not
	"""
	token_req: httpx.Response = await client.get(
		WIKI_API,
		params={"action": "query", "meta": "tokens", "type": "login", "format": "json"},
	)
	token_req.raise_for_status()

	login_token: dict = token_req.json()["query"]["tokens"]["logintoken"]
	login_req: httpx.Response = await client.post(
		WIKI_API,
		data={
			"action": "login",
			"lgname": WIKIBOT_USER,
			"lgpassword": WIKIBOT_PASSWORD,
			"lgtoken": login_token,
			"format": "json",
		},
	)
	login_req.raise_for_status()

	returned_json: dict = login_req.json()["login"]
	if returned_json and returned_json["result"] == "Success":
		global bot_authenticated

		bot_authenticated = True
		logger.info("Bot was authenticated successfully!")
	else:
		bot_authenticated = False
		logger.warning("Bot was unable to authenticate!")


def headers_formatting(
	new_etag: str | None = None, new_last_modified: str | None = None
) -> dict[str, str]:
	"""
	Formats and returns a header file for a wikithought request

	Args:
		new_etag(str | None): The optional new etag to be globalized
		new_last_modified(str | None): The optional new last modified to be globalized

	Returns:
		dict[str,str]: The new headers to be applied
	"""
	global etag, last_modifed

	headers: dict[str, str] = {}

	if new_etag:
		etag = new_etag

	if new_last_modified:
		last_modifed = new_last_modified

	if etag:
		headers["If-None-Match"] = etag
	if last_modifed:
		headers["If-Modified-Since"] = last_modifed

	return headers


def needs_category_refresh(update_time: datetime) -> bool:
	"""
	Verifys if the wikithoughts needs to be updated, checking bot status, cache and time

	Args:
		update_time (datetime): The datetime to be compared against the cache

	Returns:
		bool: if the cache needs to be refreshed
	"""

	if not bot_authenticated:
		logger.warning("Bot is not authenticated, cancelling fetch of category pages")
		return False

	return not (
		len(page_title_cache) > 0
		and last_updated_time
		and update_time < last_updated_time + timedelta(minutes=10)
	)


def process_category_page(r_json: dict[str, str]) -> tuple[list[str], bool | str]:
	"""
	Processes a wikithoughts response into a list of title pages

	Args:
		r_json (dict[str,str]): The JSON from the wiki to be processed

	Returns:
		tuple[list[str], bool | str]: The list of titles from the request, along with a possible continutation if needed
	"""
	titles: list[str] = []
	if "query" in r_json:
		for page in r_json["query"]["categorymembers"]:
			titles.append(page["title"])

		# Loop to keep everything going
		if "continue" in r_json:
			return (titles, r_json["continue"]["cmcontinue"])

		return (titles, False)
	else:
		logger.warning(f"Failure in obtaining info, JSON:\n{r_json}")
		return (titles, False)


async def fetch_category_pages(response: httpx.Response) -> list[str]:
	"""
	Loops through and gets the list of every page for Jumpstart Curated

	Args:
		response (httpx.Response): The response to be converted and searched through

	Returns:
		list[str]: The list of titles to be fetched.
	"""

	params: dict[str, str] = {
		"action": "query",
		"list": "categorymembers",
		"cmtitle": f"Category:{WIKI_CATEGORY}",
		"cmlimit": "500",
		"format": "json",
	}

	titles_found: list[str] = []

	while True:
		r_json: dict[str, str] = response.json()

		if "error" in r_json and r_json["error"].get("code") in (
			"readapidenied",
			"notloggedin",
		):
			if failed_authentication_attempts > REAUTHENTICATE_ATTEMPTS:
				logger.warning(
					"Reauthenticating the wikithought bot failed, sending empty response"
				)
				return []

			logger.info("Bot was unauthenticated, attempting to reauthenticate!")
			await auth_bot()
			if not (bot_authenticated):
				logger.warning(
					f"Failed to reauthenticate the bot! Attempt: {failed_authentication_attempts}"
				)

			failed_authentication_attempts += 1
			continue

		added, repeat_req = process_category_page(r_json)
		titles_found += added

		if repeat_req not in (None, False, ""):
			params["cmcontinue"] = repeat_req

			response = await client.get(WIKI_API, params=params)
			continue
		break
	return titles_found


async def refresh_category_pages() -> list[str]:
	"""
	Refreshes all pages of the category

	Args:
	    category (str): The name of the category to search through

	Returns:
	    list[str]
		: All the page titles found in this category, None if the bot is not authorized
	"""
	global page_title_cache, last_updated_time, queued_pages, shown_pages
	time_now: datetime = datetime.now()

	if not needs_category_refresh(time_now):
		return page_title_cache

	titles: list[str] = []
	params: dict[str, str] = {
		"action": "query",
		"list": "categorymembers",
		"cmtitle": f"Category:{WIKI_CATEGORY}",
		"cmlimit": "500",
		"format": "json",
	}

	headers: dict[str, str] = headers_formatting()
	response: httpx.Response = await client.get(
		WIKI_API, params=params, headers=headers
	)

	if response.status_code == 304:
		last_updated_time = time_now
		return page_title_cache

	elif response.status_code == 200:
		titles = await fetch_category_pages(response=response)
	else:
		logger.warning("Failed to update the CSH wiki page!")
		return page_title_cache

	last_updated_time = time_now
	page_title_cache = titles
	queued_pages = titles.copy()

	random.shuffle(queued_pages)
	shown_pages = []

	await refresh_page_dictionary()
	return page_title_cache


async def refresh_page_dictionary() -> None:
	"""
	Fetches the pages based off the cache of page titles, and updates the page cache accordingly
	"""
	global page_dict_cache, page_title_cache

	if not page_title_cache:
		return

	results: dict[str, str] = {}
	tasks: list = []
	for batch in batch_iterable(page_title_cache, BATCH_SIZE):
		params = {
			"action": "query",
			"prop": "revisions",
			"rvprop": "content",
			"rvslots": "main",
			"titles": "|".join(batch),
			"explaintext": True,
			"format": "json",
		}
		tasks.append(client.get(WIKI_API, params=params, timeout=10))
	# Code for running all this async? Pretty sure this works
	responses = await asyncio.gather(*tasks)

	for r in responses:
		r_json = r.json()
		if "query" in r_json:
			for page in r_json["query"]["pages"].values():
				wikitext = page["revisions"][0]["slots"]["main"]["*"]
				cleaned_text = clean_wikitext(wikitext)  # unfuck the text

				paragraphs = cleaned_text.split("\n\n")  # Cut the first line
				first_paragraph = (
					paragraphs[0].strip() if paragraphs else ""
				)  # Incase nick messes up?

				results[page["title"]] = first_paragraph
		else:
			logger.warning(
				f"Failure in refreshing the wiki page dictionary, JSON:\n{r_json}"
			)
			results = {"ERROR": "ERROR"}

	page_dict_cache = results


def reset_queues() -> None:
	"""
	Swaps Queued and Shown pages queued
	"""
	global queued_pages, shown_pages
	logger.info("RESETING QUEUES FOR WIKITHOUGHTS")
	if len(queued_pages) > 0:
		return

	queued_pages = shown_pages
	random.shuffle(queued_pages)
	shown_pages = []


async def get_next_display() -> dict[str, str]:
	"""
	Returns the next wiki page to be displayed in JSON Form, with the keys "page" as the title of the page
	and "content" as the first paragraph on the page

	Returns:
		dict["page": str,"content": str]: The JSON of the page name and the first paragraph
	"""
	global queued_pages, shown_pages, page_last_updated, current_page

	if page_last_updated and (
		page_last_updated < datetime.now() + timedelta(seconds=CYCLE_DEBOUNCE_TIME)
	):
		logger.warning("Pulling from quote cache!")
		return current_page

	await refresh_category_pages()

	queue_empty: bool = len(queued_pages) == 0
	if queue_empty and len(shown_pages) == 0:
		logger.warning("Error, queue and shown pages are both empty!")
		current_page = {
			"page": "ERROR GETTING PAGE",
			"content": "ERROR FETCHING CONTENT",
		}
		return current_page

	elif queue_empty:
		reset_queues()
		queue_empty = False

	new_page: str = queued_pages.pop()

	if queue_empty:
		reset_queues()

	shown_pages.append(new_page)

	if new_page in page_dict_cache:
		new_content = page_dict_cache[new_page]
		current_page = {"page": new_page, "content": new_content}
	else:
		current_page = {"page": new_page, "content": "ERROR FETCHING CONTENT"}

	return current_page
