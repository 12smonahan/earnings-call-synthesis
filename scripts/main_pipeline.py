"""Daily driver script for the scheduled GitHub Action pipeline."""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable, List

import yaml

from earnings_call.env import get_int_env
from earnings_call.pipeline import generate_and_email_transcript


@dataclass
class TickerConfig:
    """Configuration for a single ticker entry."""

    symbol: str
    company: str
    earnings_date: date
    recipients: List[str]
    next_earnings_date: date | None = None

    @classmethod
    def from_dict(cls, raw: dict) -> "TickerConfig":
        return cls(
            symbol=raw["symbol"],
            company=raw["company"],
            earnings_date=_parse_date(raw["earnings_date"]),
            recipients=list(raw.get("recipients", [])),
            next_earnings_date=_parse_optional_date(raw.get("next_earnings_date")),
        )

    def to_dict(self) -> dict:
        data = {
            "symbol": self.symbol,
            "company": self.company,
            "earnings_date": self.earnings_date.isoformat(),
            "recipients": self.recipients,
        }
        if self.next_earnings_date:
            data["next_earnings_date"] = self.next_earnings_date.isoformat()
        return data


DEFAULT_INTERVAL_DAYS = 90


def _parse_date(raw: str) -> date:
    return date.fromisoformat(raw)


def _parse_optional_date(raw: str | None) -> date | None:
    return date.fromisoformat(raw) if raw else None


def _load_config(path: Path) -> list[TickerConfig]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    tickers = payload.get("tickers", [])
    return [TickerConfig.from_dict(item) for item in tickers]


def _save_config(path: Path, tickers: Iterable[TickerConfig]) -> None:
    payload = {"tickers": [ticker.to_dict() for ticker in tickers]}
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _roll_forward_dates(entry: TickerConfig, interval_days: int = DEFAULT_INTERVAL_DAYS) -> None:
    next_date = entry.next_earnings_date or entry.earnings_date + timedelta(days=interval_days)
    subsequent = next_date + timedelta(days=interval_days)
    entry.earnings_date = next_date
    entry.next_earnings_date = subsequent


def _run_pipeline(entry: TickerConfig, *, sender: str, smtp_host: str, smtp_port: int,
                  smtp_username: str | None, smtp_password: str | None, transcript_api_key: str | None,
                  model: str, max_output_tokens: int) -> None:
    generate_and_email_transcript(
        symbol=entry.symbol,
        company=entry.company,
        sender=sender,
        recipients=entry.recipients,
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_username=smtp_username,
        smtp_password=smtp_password,
        subject=f"{entry.company} earnings call summary ({entry.symbol})",
        transcript_api_key=transcript_api_key,
        model=model,
        max_output_tokens=max_output_tokens,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the daily earnings call pipeline")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/tickers.yml"),
        help="Path to ticker configuration YAML",
    )
    parser.add_argument(
        "--interval-days",
        type=int,
        default=DEFAULT_INTERVAL_DAYS,
        help="Days between expected earnings calls (used to roll dates forward)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4.1",
        help="Model to use for summarization",
    )
    parser.add_argument(
        "--max-output-tokens",
        type=int,
        default=16000,
        help="Maximum tokens for summary generation",
    )
    args = parser.parse_args()

    sender = os.environ["SENDER_EMAIL"]
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = get_int_env("SMTP_PORT", 587)
    smtp_username = os.environ.get("SMTP_USERNAME")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    transcript_api_key = os.environ.get("RAPIDAPI_KEY")

    config_path = args.config
    tickers = _load_config(config_path)
    if not tickers:
        print("No tickers configured; exiting.")
        return

    yesterday = date.today() - timedelta(days=1)
    processed: list[TickerConfig] = []

    for entry in tickers:
        if entry.earnings_date != yesterday:
            continue
        if not entry.recipients:
            print(f"Skipping {entry.symbol}: no recipients configured")
            continue

        print(f"Processing {entry.symbol} for earnings date {entry.earnings_date}")
        _run_pipeline(
            entry,
            sender=sender,
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_username=smtp_username,
            smtp_password=smtp_password,
            transcript_api_key=transcript_api_key,
            model=args.model,
            max_output_tokens=args.max_output_tokens,
        )
        _roll_forward_dates(entry, interval_days=args.interval_days)
        processed.append(entry)

    if not processed:
        print("No tickers matched yesterday's earnings date; no updates saved.")
        return

    _save_config(config_path, tickers)
    print(f"Processed {len(processed)} ticker(s) and updated configuration.")


if __name__ == "__main__":
    main()
