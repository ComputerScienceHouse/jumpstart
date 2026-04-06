import sys
import asyncio
import importlib


def import_slack_module(monkeypatch) -> object:
	"""
	Helper function to import the slack module after setting the SLACK_API_TOKEN environment variable.

	Args:
	    monkeypatch: The pytest monkeypatch fixture.

	Returns:
	            object: The imported config module.
	"""

	monkeypatch.setenv("SLACK_API_TOKEN", "test-token")

	sys.modules.pop("config", None)
	sys.modules.pop("core.slack", None)

	importlib.import_module("config")

	return importlib.import_module("core.slack")


def test_clean_text_and_convert_response(monkeypatch):
	"""
	Test the clean_text and convert_user_response_to_bool functions in the slack module.

	Args:
	    monkeypatch: The pytest monkeypatch fixture.
	"""

	slack = import_slack_module(monkeypatch)

	raw = "<b>Hello</b> *world* _there_ `code` &lt;skip&gt;"
	cleaned = slack.clean_text(raw)
	assert "<" not in cleaned
	assert "*" not in cleaned
	assert "_" not in cleaned
	assert "`" not in cleaned

	yes_payload = {"actions": [{"action_id": "yes_j"}]}
	no_payload = {"actions": [{"action_id": "no_j"}]}
	assert slack.convert_user_response_to_bool(yes_payload) is True
	assert slack.convert_user_response_to_bool(no_payload) is False
	# malformed payload
	assert slack.convert_user_response_to_bool({}) is False


def test_gather_emojis_success_and_failure(monkeypatch):
	"""
	Test the gather_emojis function in the slack module.

	Args:
	    monkeypatch: The pytest monkeypatch fixture.
	"""

	slack = import_slack_module(monkeypatch)

	class FakeClientSuccess:
		async def emoji_list(self):
			return {"ok": True, "emoji": {"smile": "url"}}

	monkeypatch.setattr(slack, "client", FakeClientSuccess())
	emojis = asyncio.run(slack.gather_emojis())
	assert emojis == {"smile": "url"}

	class FakeClientFail:
		async def emoji_list(self):
			raise RuntimeError("boom")

	monkeypatch.setattr(slack, "client", FakeClientFail())
	emojis = asyncio.run(slack.gather_emojis())
	assert emojis == {}

	monkeypatch.setattr(slack, "client", None)
	emojis = asyncio.run(slack.gather_emojis())
	assert emojis == {}


def test_request_upload_via_dm_success_and_exception(monkeypatch):
	"""
	Test the request_upload_via_dm function in the slack module.

	Args:
	    monkeypatch: The pytest monkeypatch fixture.
	"""

	slack = import_slack_module(monkeypatch)

	monkeypatch.setattr(
		slack,
		"SLACK_DM_TEMPLATE",
		[{"text": {"text": ""}}, {"elements": [{"value": ""}]}],
	)

	recorded = {}

	class FakeClient:
		async def conversations_open(self, *, users):
			return {"ok": True, "channel": {"id": "FAKE_CHANNEL"}}

		async def chat_postMessage(self, *, channel, text, blocks):
			recorded["channel"] = channel
			recorded["text"] = text
			recorded["blocks"] = blocks

	monkeypatch.setattr(slack, "client", FakeClient())

	asyncio.run(slack.request_upload_via_dm("U123", "Announcement!"))
	assert recorded["channel"] == "U123"
	assert recorded["text"] == slack.SLACK_JUMPSTART_MESSAGE

	assert isinstance(recorded["blocks"], list)
	assert "Announcement!" in recorded["blocks"][0]["text"]["text"]

	class BrokenClient:
		async def chat_postMessage(self, **_):
			raise RuntimeError("nope")

	monkeypatch.setattr(slack, "client", BrokenClient())

	asyncio.run(slack.request_upload_via_dm("U123", "Announcement!"))


def test_get_and_add_announcement(monkeypatch):
	"""
	Test the get_announcement and add_announcement functions in the slack module.

	Args:
	    monkeypatch: The pytest monkeypatch fixture.
	"""

	slack = import_slack_module(monkeypatch)

	slack.announcements.clear()
	assert slack.get_announcement() is None

	skip_announcements: list[str | None] = [None, "", "   "]
	for ann in skip_announcements:
		slack.add_announcement(ann)

	assert slack.get_announcement() is None

	test_announcements: list[str] = ["First", "Second", "Third"]

	for ann in test_announcements:
		slack.add_announcement(ann)

	for ann in test_announcements:
		assert slack.get_announcement() == ann

	assert (
		slack.get_announcement() == test_announcements[-1]
	)  # should return last announcement when queue is empty
