import sys
import importlib

import pytest


def import_config_module() -> object:
	"""
	Helper function to import the config module after modifying environment variables.
	"""

	if "config" in sys.modules:
		del sys.modules["config"]

	return importlib.import_module("config")


def test_missing_slack_token_raises(monkeypatch) -> None:
	"""
	Test that if SLACK_API_TOKEN is missing, an exception is raised.

	Args:
	    monkeypatch: The pytest monkeypatch fixture.
	"""

	# Ensure SLACK_API_TOKEN is not set
	monkeypatch.delenv("SLACK_API_TOKEN", raising=False)
	# Prevent leftover module from interfering
	sys.modules.pop("config", None)

	with pytest.raises(Exception, match="Missing SLACK_API_TOKEN"):
		import_config_module()


def test_with_slack_token_parses_values(monkeypatch) -> None:
	"""
	Test that with a valid SLACK_API_TOKEN, the config values are parsed correctly.

	Args:
	    monkeypatch: The pytest monkeypatch fixture.
	"""

	monkeypatch.setenv("SLACK_API_TOKEN", "test-token")
	monkeypatch.setenv("WATCHED_CHANNELS", "chan1,chan2")
	monkeypatch.setenv("CALENDAR_OUTLOOK_DAYS", "5")
	monkeypatch.setenv("CALENDAR_EVENT_MAXIMUM", "20")
	monkeypatch.setenv("CALENDAR_TIMEZONE", "UTC")
	monkeypatch.setenv("CALENDAR_CACHE_REFRESH", "15")

	sys.modules.pop("config", None)
	cfg = import_config_module()

	assert cfg.SLACK_API_TOKEN == "test-token"
	assert cfg.WATCHED_CHANNELS == ("chan1", "chan2")
	assert cfg.CALENDAR_OUTLOOK_DAYS == 5
	assert cfg.CALENDAR_EVENT_MAXIMUM == 20
	assert cfg.CALENDAR_TIMEZONE == "UTC"
	assert isinstance(cfg.SLACK_DM_TEMPLATE, dict)
