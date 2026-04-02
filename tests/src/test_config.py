import sys
import importlib


def import_config_module() -> object:
	"""
	Helper function to import the config module after modifying environment variables.

	Returns:
		object: The imported config module.
	"""

	if "config" in sys.modules:
		del sys.modules["config"]

	return importlib.import_module("config")


def test_get_env_variable(monkeypatch) -> None:
	"""
	Test the _get_env_variable function to ensure it retrieves environment variables correctly.

	Args:
	    monkeypatch: The pytest monkeypatch fixture.
	"""

	monkeypatch.setenv("TEST_ENV_VAR", "test_value")
	cfg = import_config_module()

	assert cfg._get_env_variable("TEST_ENV_VAR", None) == "test_value"
	assert cfg._get_env_variable("NON_EXISTENT_VAR", "default_value") == "default_value"
	assert cfg._get_env_variable("NON_EXISTENT_VAR", None) is None


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
