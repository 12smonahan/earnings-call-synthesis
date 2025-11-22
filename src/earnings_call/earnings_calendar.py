"""Fetch and persist upcoming earnings call dates via RapidAPI."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Sequence

import requests
from dotenv import load_dotenv

load_dotenv()

HOST = "seeking-alpha.p.rapidapi.com"


@dataclass
class EarningsEvent:
    """Representation of an upcoming earnings call for a ticker."""

    symbol: str
    earnings_date: datetime
    company: Optional[str] = None

    def as_json(self) -> dict:
        payload = asdict(self)
        payload["earnings_date"] = self.earnings_date.isoformat()
        return payload


def _get_api_key(provided: Optional[str]) -> str:
    key = provided or os.getenv("RAPIDAPI_KEY")
    if not key:
        raise ValueError(
            "RapidAPI key is required. Set RAPIDAPI_KEY or pass api_key explicitly."
        )
    return key


def _extract_first_date(payload: dict) -> Optional[datetime]:
    """Attempt to pull an earnings date from common Seeking Alpha schemas."""

    data = payload.get("data")
    if isinstance(data, list) and data:
        candidate = data[0]
        attributes = candidate.get("attributes", {}) if isinstance(candidate, dict) else {}
        for field in (
            "earningsDate",
            "earningsDateUtc",
            "date",
            "reportDate",
            "startDateTime",
        ):
            raw_date = attributes.get(field) if attributes else None
            if raw_date:
                return _parse_date(raw_date)
    if isinstance(data, dict):
        for field in ("earningsDate", "date", "reportDate"):
            raw_date = data.get(field)
            if raw_date:
                return _parse_date(raw_date)
    return None


def _parse_date(value: str) -> Optional[datetime]:
    formats = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
        "%m/%d/%Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def fetch_earnings_event(symbol: str, api_key: Optional[str] = None) -> Optional[EarningsEvent]:
    """Fetch the next earnings date for a single ticker.

    Returns None if the API request fails or no date can be extracted.
    """

    key = _get_api_key(api_key)
    url = f"https://{HOST}/earnings/v2/list"
    params = {"id": symbol.lower(), "size": 1, "page": 1}
    headers = {
        "x-rapidapi-key": key,
        "x-rapidapi-host": HOST,
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=20)
    except requests.RequestException as exc:
        print(f"Error contacting earnings calendar API for {symbol}: {exc}")
        return None

    if response.status_code >= 400:
        print(
            f"Failed to fetch earnings calendar for {symbol}: {response.status_code} {response.text[:200]}"
        )
        return None

    payload = response.json()
    earnings_date = _extract_first_date(payload)
    if not earnings_date:
        print(f"No earnings date found in response for {symbol}: {payload}")
        return None

    company = None
    data = payload.get("data")
    if isinstance(data, list) and data and isinstance(data[0], dict):
        attributes = data[0].get("attributes", {})
        company = attributes.get("company") or attributes.get("name")

    return EarningsEvent(symbol=symbol.upper(), earnings_date=earnings_date, company=company)


def fetch_earnings_calendar(
    tickers: Sequence[str],
    *,
    api_key: Optional[str] = None,
    output_path: Path | str = "earnings_calendar.json",
) -> List[EarningsEvent]:
    """Pull earnings dates for tickers and persist them to a JSON file."""

    events: List[EarningsEvent] = []
    for ticker in tickers:
        event = fetch_earnings_event(ticker, api_key)
        if event:
            events.append(event)

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [event.as_json() for event in events]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return events


def load_saved_calendar(path: Path | str = "earnings_calendar.json") -> List[EarningsEvent]:
    """Load a previously saved calendar file."""

    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Calendar file not found: {file_path}")

    raw = json.loads(file_path.read_text(encoding="utf-8"))
    events: List[EarningsEvent] = []
    for item in raw:
        date_value = item.get("earnings_date")
        parsed_date = _parse_date(date_value) if isinstance(date_value, str) else None
        if not parsed_date:
            continue
        events.append(
            EarningsEvent(
                symbol=item.get("symbol", ""),
                earnings_date=parsed_date,
                company=item.get("company"),
            )
        )
    return events
