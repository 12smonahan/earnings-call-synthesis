"""Send the latest Apple earnings call transcript and summary via email."""

import os

from earnings_call.pipeline import generate_and_email_transcript, TranscriptPipelineError


def _env_flag(name: str, default: str = "true") -> bool:
    return os.getenv(name, default).strip().lower() not in {"0", "false", "no", "off"}


def main() -> None:
    recipient = os.getenv("RECIPIENT_EMAIL", "12smonahan@gmail.com")
    sender = os.getenv("SENDER_EMAIL")
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
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
            symbol="AAPL",
            company="Apple",
            sender=sender,
            recipients=[recipient],
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_username=smtp_username,
            smtp_password=smtp_password,
            use_tls=use_tls,
            transcript_api_key=os.getenv("RAPIDAPI_KEY"),
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            max_output_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "800")),
        )
    except TranscriptPipelineError as exc:
        raise SystemExit(f"Transcript pipeline failed: {exc}") from exc
    except Exception as exc:  # pragma: no cover - surfaced to user for quick debug
        raise SystemExit(f"Failed to send AAPL transcript email: {exc}") from exc


if __name__ == "__main__":
    main()
