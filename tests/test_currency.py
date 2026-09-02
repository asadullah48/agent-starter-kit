"""Tests for the apilayer-backed currency conversion tool."""

from unittest.mock import MagicMock, patch

import pytest

from tools import execute_tool
from tools.currency import convert_currency


def test_convert_currency_without_api_key_is_a_clear_error(monkeypatch):
    monkeypatch.delenv("APILAYER_API_KEY", raising=False)
    import utils.config as config_module

    config_module.get_settings.cache_clear()
    with pytest.raises(ValueError, match="APILAYER_API_KEY"):
        convert_currency(amount=10, from_currency="usd", to_currency="pkr")
    config_module.get_settings.cache_clear()


def test_execute_tool_reports_missing_key_as_is_error_not_a_crash():
    result, is_error = execute_tool(
        "convert_currency", {"amount": 10, "from_currency": "usd", "to_currency": "pkr"}
    )
    assert is_error is True
    assert "convert_currency" in result


@patch("tools.currency.httpx.get")
@patch("tools.currency.get_settings")
def test_convert_currency_happy_path(mock_settings, mock_get):
    mock_settings.return_value = MagicMock(apilayer_api_key="fake-key")
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "success": True,
        "result": 2785.5,
        "info": {"rate": 278.55},
    }
    mock_get.return_value = mock_response

    result = convert_currency(amount=10, from_currency="usd", to_currency="pkr")

    assert "10 USD" in result
    assert "2785.50 PKR" in result
