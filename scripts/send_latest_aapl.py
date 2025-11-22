"""Send the latest Upstart earnings call transcript and summary via email."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from earnings_call.env import get_int_env
from earnings_call.pipeline import generate_and_email_transcript, TranscriptPipelineError


def _env_flag(name: str, default: str = "true") -> bool:
    return os.getenv(name, default).strip().lower() not in {"0", "false", "no", "off"}


def main() -> None:
    recipient = os.getenv("RECIPIENT_EMAIL", "12smonahan@gmail.com")
    sender = os.getenv("SENDER_EMAIL")
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = get_int_env("SMTP_PORT", 587)
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    use_tls = _env_flag("SMTP_USE_TLS", "true")

    missing = [name for name, value in {"SENDER_EMAIL": sender, "SMTP_HOST": smtp_host}.items() if not value]
    if missing:
        raise SystemExit(
            "Missing required environment variables: " + ", ".join(missing)
        )

    try:
        generate_and_email_transcript(
            symbol="UPST",
            company="Upstart",
            sender=sender,
            recipients=[recipient],
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_username=smtp_username,
            smtp_password=smtp_password,
            use_tls=use_tls,
            transcript_api_key=os.getenv("RAPIDAPI_KEY"),
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            max_output_tokens=get_int_env("OPENAI_MAX_TOKENS", 8000),
        )
    except TranscriptPipelineError as exc:
        raise SystemExit(f"Transcript pipeline failed: {exc}") from exc
    except Exception as exc:  # pragma: no cover - surfaced to user for quick debug
        raise SystemExit(f"Failed to send UPST transcript email: {exc}") from exc


if __name__ == "__main__":
    main()
