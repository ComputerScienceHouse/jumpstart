import httpx
import asyncio
from datetime import datetime, timedelta
from itertools import islice
from config import WIKIBOT_PASSWORD, WIKIBOT_USER, WIKI_CATEGORY, WIKI_API
import logging
import random
import re

logging.basicConfig(level=logging.INFO)


BATCH_SIZE: int = 50  # max titles per request
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


def clean_wikitext(text: str) -> str:
	"""
	Function for cleaning markdown text to be displayed
	"""
	# [[Page|Text]] → Text
	text = re.sub(r"\[\[[^\|\]]*\|([^\]]+)\]\]", r"\1", text)

	# [[Page]] → Page
	text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)

	# Remove templates {{...}}
	text = re.sub(r"\{\{.*?\}\}", "", text, flags=re.DOTALL)

	# Remove bold/italic markup
	text = re.sub(r"''+", "", text)

	# Remove HTML tags
	text = re.sub(r"<.*?>", "", text)

	return text.strip()


def batch_iterable(iterable: list, size: int):
	"""
	Generator function for splitting up lists into smaller lists
	To be frank, found this online when researching about the MediaWiki API

	Yields:
	    A batch split by the requested size
	"""
	it = iter(iterable)
	while True:
		batch = list(islice(it, size))
		if not batch:
			break
		yield batch


async def auth_bot():
	"""
	Authenticates the CSH Wiki bot, logging if it was succesful or not
	"""
	token_req: httpx.Response = await client.get(
		WIKI_API,
		params={"action": "query", "meta": "tokens", "type": "login", "format": "json"},
	)
	token_req.raise_for_status()

	login_token: httpx.Response = token_req.json()["query"]["tokens"]["logintoken"]
	login_req = await client.post(
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
		logger.info("Bot was authenticated succesfully!")
	else:
		logger.warning("Bot was unable to authenticate!")


async def refresh_category_pages():
	"""
	Function for fetching all pages of a MediaWiki Category

	Args:
	    category (str): The name of the category to search through

	Returns:
	    list[str]: All the page titles found in this category, None if the bot is not authorized
	"""
	global \
		page_title_cache, \
		last_updated_time, \
		etag, \
		last_modifed, \
		queued_pages, \
		shown_pages

	if not bot_authenticated:
		logger.warning("Bot is not authenticated, cancelling fetch of category pages")
		return

	time_now: datetime = datetime.now()
	if (
		len(page_title_cache) > 0
		and last_updated_time
		and time_now < last_updated_time + timedelta(minutes=10)
	):
		return

	titles: list[str] = []
	params: dict[str, str] = {
		"action": "query",
		"list": "categorymembers",
		"cmtitle": f"Category:{WIKI_CATEGORY}",
		"cmlimit": "500",
		"format": "json",
	}

	headers = {}
	# This needs to loop due to mediawiki limitations
	while True:
		if not "cmcontinue" in params:
			if etag:
				headers["If-None-Match"] = etag
			if last_modifed:
				headers["If-Modified-Since"] = last_modifed
		else:
			headers = {}
		response: httpx.Response = await client.get(
			WIKI_API, params=params, headers=headers
		)

		if response.status_code == 304:
			last_updated_time = time_now
			return page_title_cache

		elif response.status_code == 200:
			etag = response.headers.get("ETag")
			last_modifed = response.headers.get("Last-Modified")

			r_json: dict[str, str] = response.json()
			for page in r_json["query"]["categorymembers"]:
				titles.append(page["title"])

			# Loop to keep everything going
			if "continue" in r_json:
				params["cmcontinue"] = r_json["continue"]["cmcontinue"]
			else:
				break
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


async def refresh_page_dictionary():
	"""
	Function for fetching the first "Sentence" of each title

	Args:
	    titles (list[str]): Each title of the page to search through

	Returns:
	    dict {title: str}: The title of each page, along with its corresponding sentence/first paragraph

	"""
	global page_dict_cache, page_title_cache

	if not page_title_cache:
		return {}

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
		for page in r_json["query"]["pages"].values():
			wikitext = page["revisions"][0]["slots"]["main"]["*"]

			cleaned_text = clean_wikitext(wikitext)  # unfuck the text

			paragraphs = cleaned_text.split("\n\n")  # Cut the first line
			first_paragraph = (
				paragraphs[0].strip() if paragraphs else ""
			)  # Incase nick messes up?

			results[page["title"]] = first_paragraph

	page_dict_cache = results


def reset_queues():
	global queued_pages, shown_pages
	"""
	Swaps Queued and Shown pages que
	"""
	queued_pages = shown_pages
	shown_pages = []


async def get_next_display():
	"""
	Returns the next wiki page to be displayed in JSON Form, with the keys "page" as the title of the page
	and "content" as the first paragraph on the page

	Returns:
		dict["page": str,"content": str]: The JSON of the page name and the first paragraph
	"""
	global queued_pages, shown_pages
	await refresh_category_pages()

	que_empty: bool = len(queued_pages) == 0
	if que_empty and len(shown_pages) == 0:
		logger.warning("ERROR?!?")
		return {"page": "ERROR GETTING PAGE", "content": "ERROR FETCHING CONTENT"}
	elif que_empty:
		reset_queues()

	new_page: str = queued_pages.pop()

	if que_empty:
		reset_queues()

	shown_pages.append(new_page)

	if new_page in page_dict_cache:
		new_content = page_dict_cache[new_page]
		return {"page": new_page, "content": new_content}

	return {"page": new_page, "content": "ERROR FETCHING CONTENT"}
