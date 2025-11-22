"""Compose and send summaries and transcripts to stakeholders via email."""

from __future__ import annotations

from email.message import EmailMessage
from pathlib import Path
from typing import Iterable, Optional
import smtplib

from fpdf import FPDF


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

    def _make_pdf(transcript_text: str, transcript_file: Path) -> Path:
        output_dir = Path("transcript_pdfs")
        output_dir.mkdir(parents=True, exist_ok=True)

        pdf_path = output_dir / f"{transcript_file.stem}.pdf"

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Earnings Call Transcript", ln=True)
        pdf.set_font("Helvetica", "", 11)
        pdf.ln(4)

        for line in transcript_text.splitlines():
            content = line.strip() or " "
            pdf.multi_cell(0, 7, content)

        pdf.output(pdf_path)
        return pdf_path

    pdf_attachment = _make_pdf(transcript, path)

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = ", ".join(recipients_list)
    message.set_content(summary_text)

    message.add_attachment(
        pdf_attachment.read_bytes(),
        maintype="application",
        subtype="pdf",
        filename=pdf_attachment.name,
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
