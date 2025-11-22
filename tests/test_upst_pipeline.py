"""Integration test to send Upstart earnings call summary and transcript."""

from __future__ import annotations

import os
from email.message import EmailMessage

import pytest

from earnings_call.pipeline import generate_and_email_transcript


@pytest.mark.integration
@pytest.mark.filterwarnings("ignore::UserWarning")
def test_upst_pipeline_emails_summary_and_transcript(monkeypatch: pytest.MonkeyPatch) -> None:
    """End-to-end exercise of the UPST pipeline using live services.

    Requires the following environment variables:
    - RAPIDAPI_KEY: access token for fetching the latest transcript.
    - OPENAI_API_KEY: access token for summary generation.
    - SMTP_HOST / SMTP_PORT / SMTP_USERNAME / SMTP_PASSWORD: SMTP credentials.
    - SENDER_EMAIL: email address used as the sender.
    """

    required_env = {
        "RAPIDAPI_KEY": os.getenv("RAPIDAPI_KEY"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "SMTP_HOST": os.getenv("SMTP_HOST"),
        "SMTP_PORT": os.getenv("SMTP_PORT"),
        "SMTP_USERNAME": os.getenv("SMTP_USERNAME"),
        "SMTP_PASSWORD": os.getenv("SMTP_PASSWORD"),
        "SENDER_EMAIL": os.getenv("SENDER_EMAIL"),
    }

    missing = [name for name, value in required_env.items() if not value]
    if missing:
        pytest.fail(
            "Missing required environment variables for UPST integration test: "
            + ", ".join(sorted(missing))
        )

    captured: dict[str, EmailMessage] = {}

    def _capture_send_email(message: EmailMessage, *, smtp_host: str, smtp_port: int, username: str | None, password: str | None, use_tls: bool) -> None:
        captured["message"] = message

    monkeypatch.setattr("earnings_call.pipeline.send_email", _capture_send_email)

    summary = generate_and_email_transcript(
        symbol="UPST",
        company="Upstart",
        sender=required_env["SENDER_EMAIL"],
        recipients=["12smonahan@gmail.com"],
        smtp_host=required_env["SMTP_HOST"],
        smtp_port=int(required_env["SMTP_PORT"]),
        smtp_username=required_env["SMTP_USERNAME"],
        smtp_password=required_env["SMTP_PASSWORD"],
        transcript_api_key=required_env["RAPIDAPI_KEY"],
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    )

    assert summary.summary_text.strip(), "Summary text should not be empty"
    assert summary.transcript_path.exists(), "Transcript file should exist on disk"

    message = captured.get("message")
    assert isinstance(message, EmailMessage), "Pipeline did not attempt to send an email"

    attachments = list(message.iter_attachments())
    assert len(attachments) >= 2, "Email should contain at least summary and transcript PDFs"

    filenames = {part.get_filename() for part in attachments}
    assert any(name and name.endswith("_summary.pdf") for name in filenames), "Summary PDF missing"
    assert any(
        name and name.endswith(".pdf") and not name.endswith("_summary.pdf") for name in filenames
    ), "Transcript PDF missing"
