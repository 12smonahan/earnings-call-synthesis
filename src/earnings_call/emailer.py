"""Compose and send summaries and transcripts to stakeholders via email."""

from __future__ import annotations

from email.message import EmailMessage
from pathlib import Path
from typing import Iterable, Optional
import smtplib


def build_email(
    *,
    subject: str,
    sender: str,
    recipients: Iterable[str],
    summary_text: str,
    transcript_path: Path | str,
) -> EmailMessage:
    """Build an email containing the summary and transcript attachment.

    The email body contains the synthesized summary. The full transcript is attached
    as a plain-text file so recipients can audit or pull additional quotes.
    """

    path = Path(transcript_path)
    if not path.exists():
        raise FileNotFoundError(f"Transcript file not found: {path}")

    recipients_list = list(recipients)
    if not recipients_list:
        raise ValueError("At least one recipient email is required.")

    transcript = path.read_text(encoding="utf-8")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = ", ".join(recipients_list)
    message.set_content(summary_text)

    message.add_attachment(
        transcript,
        maintype="text",
        subtype="plain",
        filename=path.name,
    )

    return message


def send_email(
    message: EmailMessage,
    *,
    smtp_host: str,
    smtp_port: int = 587,
    username: Optional[str] = None,
    password: Optional[str] = None,
    use_tls: bool = True,
) -> None:
    """Send the provided email message via SMTP.

    Args:
        message: The prepared :class:`EmailMessage` with recipients populated.
        smtp_host: SMTP server host name.
        smtp_port: SMTP port (defaults to 587 for TLS).
        username: Optional username for authenticated SMTP.
        password: Optional password for authenticated SMTP.
        use_tls: Whether to start TLS before sending the message.
    """

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        if use_tls:
            server.starttls()
        if username and password:
            server.login(username, password)
        server.send_message(message)
