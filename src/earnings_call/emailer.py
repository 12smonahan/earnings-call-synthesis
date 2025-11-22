"""Compose and send summaries and transcripts to stakeholders via email."""

from __future__ import annotations

from email.message import EmailMessage
from pathlib import Path
from typing import Iterable, Optional
import re
import smtplib

from fpdf import FPDF


def _sanitize_pdf_text(text: str) -> str:
    """Strip characters outside Latin-1 to keep FPDF core fonts happy."""

    return text.encode("latin-1", "ignore").decode("latin-1")


def build_email(
    *,
    subject: str,
    sender: str,
    recipients: Iterable[str],
    summary_text: str,
    transcript_path: Path | str,
    company: str,
    symbol: str,
) -> EmailMessage:
    """Build an email containing a formatted summary PDF and transcript PDF.

    The email body calls out the company, call date, attachment contents, and a concise
    four-sentence overview so recipients know what to expect before opening files.
    """

    path = Path(transcript_path)
    if not path.exists():
        raise FileNotFoundError(f"Transcript file not found: {path}")

    recipients_list = list(recipients)
    if not recipients_list:
        raise ValueError("At least one recipient email is required.")

    transcript = path.read_text(encoding="utf-8")

    def _parse_summary_sections(summary: str) -> list[tuple[str, str]]:
        header_regex = re.compile(r"(?m)^\s*(\d+\)\s+[^\n]+)")
        matches = list(header_regex.finditer(summary))
        sections: list[tuple[str, str]] = []

        if not matches:
            return sections

        for idx, match in enumerate(matches):
            start = match.end()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(summary)
            body = summary[start:end].strip()
            body = re.sub(r"(?m)^=+\s*$", "", body).strip()
            sections.append((match.group(1).strip(), body))

        return sections

    def _extract_call_date(transcript_file: Path) -> Optional[str]:
        match = re.search(r"_(\d{4}-\d{2}-\d{2})", transcript_file.stem)
        return match.group(1) if match else None

    def _make_summary_pdf(summary: str, transcript_file: Path) -> Path:
        output_dir = Path("summary_pdfs")
        output_dir.mkdir(parents=True, exist_ok=True)

        pdf_path = output_dir / f"{transcript_file.stem}_summary.pdf"

        class SummaryPDF(FPDF):
            """PDF helper for nicely formatted summaries."""

        pdf = SummaryPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, _sanitize_pdf_text(f"{company} Earnings Call Summary"), ln=True)

        call_date = _extract_call_date(transcript_file)
        meta_line = f"Symbol: {symbol}"
        if call_date:
            meta_line += f" | Call Date: {call_date}"
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 8, _sanitize_pdf_text(meta_line), ln=True)
        pdf.ln(6)

        parsed_sections = _parse_summary_sections(summary)

        if parsed_sections:
            for idx, (header, body) in enumerate(parsed_sections):
                if idx > 0:
                    pdf.add_page()
                pdf.set_font("Helvetica", "B", 12)
                pdf.cell(0, 8, _sanitize_pdf_text(header), ln=True)
                pdf.ln(2)

                pdf.set_font("Helvetica", "", 11)
                paragraphs = [
                    block.strip()
                    for block in re.split(r"\n\s*\n", body)
                    if block.strip()
                ]
                if not paragraphs and body:
                    paragraphs = [body]

                for paragraph in paragraphs:
                    pdf.multi_cell(0, 7, _sanitize_pdf_text(paragraph))
                    pdf.ln(3)
        else:
            pdf.set_font("Helvetica", "", 11)
            paragraphs = [
                block.strip()
                for block in re.split(r"\n\s*\n", summary)
                if block.strip()
            ]
            if not paragraphs and summary.strip():
                paragraphs = [summary.strip()]

            for paragraph in paragraphs:
                pdf.multi_cell(0, 7, _sanitize_pdf_text(paragraph))
                pdf.ln(3)

        pdf.output(pdf_path)
        return pdf_path

    def _make_transcript_pdf(transcript_text: str, transcript_file: Path) -> Path:
        output_dir = Path("transcript_pdfs")
        output_dir.mkdir(parents=True, exist_ok=True)

        pdf_path = output_dir / f"{transcript_file.stem}.pdf"
        if pdf_path.exists():
            return pdf_path

        class TranscriptPDF(FPDF):
            """PDF helper for raw transcript text."""

        pdf = TranscriptPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, _sanitize_pdf_text(f"{company} Earnings Call Transcript"), ln=True)

        call_date = _extract_call_date(transcript_file)
        meta_line = f"Symbol: {symbol}"
        if call_date:
            meta_line += f" | Call Date: {call_date}"
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 8, _sanitize_pdf_text(meta_line), ln=True)
        pdf.ln(4)

        pdf.set_font("Helvetica", "", 10)
        for line in transcript_text.splitlines():
            cleaned = line.rstrip()
            if not cleaned:
                pdf.ln(4)
                continue
            pdf.multi_cell(0, 6, _sanitize_pdf_text(cleaned))

        pdf.output(pdf_path)
        return pdf_path

    def _high_level_summary(summary: str) -> str:
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", summary) if s.strip()]
        if not sentences:
            return "Summary unavailable."
        return " ".join(sentences[:4])

    pdf_attachment = _make_summary_pdf(summary_text, path)
    transcript_pdf_attachment = _make_transcript_pdf(transcript, path)

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = ", ".join(recipients_list)
    call_date = _extract_call_date(path)
    body_lines = [
        f"Attached are the summary and full transcript for {company} ({symbol}).",
        f"Earnings call date: {call_date or 'Unknown'}.",
        "",
        "Attachments:",
        f"- {pdf_attachment.name}: formatted PDF summary",
        f"- {transcript_pdf_attachment.name}: PDF version of the full transcript",
        "",
        "High-level summary (4 sentences):",
        _high_level_summary(summary_text),
    ]

    message.set_content("\n".join(body_lines))

    message.add_attachment(
        pdf_attachment.read_bytes(),
        maintype="application",
        subtype="pdf",
        filename=pdf_attachment.name,
    )

    message.add_attachment(
        transcript_pdf_attachment.read_bytes(),
        maintype="application",
        subtype="pdf",
        filename=transcript_pdf_attachment.name,
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
