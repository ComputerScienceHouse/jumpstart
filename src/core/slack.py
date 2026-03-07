import re
import json

from logging import getLogger, Logger

from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError

from config import SLACK_API_TOKEN, SLACK_JUMPSTART_MESSAGE, SLACK_DM_TEMPLATE


logger: Logger = getLogger(__name__)

client: AsyncWebClient = AsyncWebClient(token=SLACK_API_TOKEN)

announcements: list[str] = ["Welcome to Jumpstart!"]


def clean_text(raw: str) -> str:
    """
    Strip Slack mrkdwn, HTML entities, and formatting characters.

    Args:
        raw: The raw text to be cleaned.
    """

    text: str = re.sub(r"<[^>]+>", "", str(raw), flags=re.IGNORECASE)
    text: str = re.sub(r"&lt;.*?&gt;", "", text, flags=re.IGNORECASE)
    return text. replace("*", ""). replace("_", ""). replace("`", "").strip()


async def gather_emojis() -> dict:

    logger.info("Gathering emojis from slack!")
    
    try:
        emoji_request: dict = await client.emoji_list()
        assert emoji_request.get("ok", False)

        return emoji_request.get("emoji", {})
    except Exception as e:
        logger.error(f"Error gathering emojis: {e}")
    
    return {}


async def request_upload_via_dm(user_id: str, announcement_text: str) -> None:

    logger.info("Requesting upload announcement permission!")

    try:
        message: dict = SLACK_DM_TEMPLATE.copy()
        
        message[0]["text"]["text"] += announcement_text
        message[1]["elements"][0]["value"] = {"text": announcement_text, "user": user_id}

        await client.chat_postMessage(channel=user_id, text=SLACK_JUMPSTART_MESSAGE, blocks=message)
    except Exception as e:
        logger.error(f"Error messaging user {user_id}: {e}")


def convert_user_response_to_bool(message_data: dict) -> bool:

    user_response: bool = False

    try:
        user_response = message_data.get("actions", []).get(0, {}).get("action_id", "no_j") == "yes_j"
    except Exception as e:
        logger.error(f"Failed to parse data: {e}")

    return user_response


def get_announcement() -> str | None:
    if len(announcements) == 0:
        return None
    
    if len(announcements) == 1:
        return announcements[0]

    return announcements.pop(0)


def add_announcement(announcement_text: str) -> None:
    if announcement_text is None or announcement_text.strip() == "":
        logger.warning("Attempted to add empty announcement, skipping!")
        return
    
    announcements.append(announcement_text)