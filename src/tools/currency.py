"""A currency-conversion tool using the apilayer.com Exchange Rates Data API.

Free tier: sign up at
https://apilayer.com/marketplace/exchangerates_data-api, grab the key
from your dashboard, and set APILAYER_API_KEY in .env. This is the
pattern for any other apilayer product too (weather, IP geolocation,
phone number validation, ...) -- swap the URL and response parsing,
keep everything else (settings lookup, error handling, tool schema).
"""

from __future__ import annotations

import httpx

from utils.config import get_settings

TOOL_DEF = {
    "name": "convert_currency",
    "description": (
        "Convert an amount from one currency to another using live "
        "exchange rates. Use this instead of guessing exchange rates."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "amount": {"type": "number", "description": "The amount to convert."},
            "from_currency": {
                "type": "string",
                "description": "3-letter source currency code, e.g. USD.",
            },
            "to_currency": {
                "type": "string",
                "description": "3-letter target currency code, e.g. PKR.",
            },
        },
        "required": ["amount", "from_currency", "to_currency"],
    },
}

_BASE_URL = "https://api.apilayer.com/exchangerates_data/convert"


def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert `amount` from `from_currency` to `to_currency` and describe the result."""
    settings = get_settings()
    if not settings.apilayer_api_key:
        raise ValueError(
            "APILAYER_API_KEY is not set. Get a free key at "
            "https://apilayer.com/marketplace/exchangerates_data-api and "
            "add it to .env."
        )

    params = {"to": to_currency.upper(), "from": from_currency.upper(), "amount": amount}
    headers = {"apikey": settings.apilayer_api_key}

    response = httpx.get(_BASE_URL, params=params, headers=headers, timeout=15.0)
    response.raise_for_status()
    data = response.json()

    if not data.get("success", True):
        raise ValueError(data.get("error", {}).get("info", "conversion failed"))

    result = data["result"]
    rate = data["info"]["rate"]
    return f"{amount} {from_currency.upper()} = {result:.2f} {to_currency.upper()} (rate: {rate})"
