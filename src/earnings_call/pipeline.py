"""End-to-end orchestration for fetching, summarizing, and emailing transcripts."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

from openai import OpenAI

from fetch_transcript import fetch_latest_transcript
from earnings_call.emailer import build_email, send_email
from earnings_call.summarizer import TranscriptSummary, synthesize_transcript


class TranscriptPipelineError(RuntimeError):
    """Raised when any step of the transcript pipeline fails."""


def generate_and_email_transcript(
    *,
    symbol: str,
    company: str,
    sender: str,
    recipients: Iterable[str],
    smtp_host: str,
    smtp_port: int = 587,
    smtp_username: Optional[str] = None,
    smtp_password: Optional[str] = None,
    use_tls: bool = True,
    subject: Optional[str] = None,
    transcript_api_key: Optional[str] = None,
    transcript_path: Optional[Path | str] = None,
    model: str = "gpt-4o-mini",
    client: Optional[OpenAI] = None,
    max_output_tokens: int = 800,
    extra_instructions: Optional[Iterable[str]] = None,
    transcript_text_override: Optional[str] = None,
) -> TranscriptSummary:
    """Fetch, summarize, and email a transcript.

    The function fetches the latest transcript for the ticker (unless a path or text
    override is provided), generates an OpenAI summary, and emails both the summary
    and full transcript to stakeholders.
    """

    transcript_file: Optional[Path] = None
    if transcript_text_override:
        # Allow callers to inject raw text instead of reading from disk.
        transcript_file = Path(transcript_path or f"transcripts/{symbol}_transcript.txt")
        transcript_file.parent.mkdir(parents=True, exist_ok=True)
        transcript_file.write_text(transcript_text_override, encoding="utf-8")
    elif transcript_path:
        transcript_file = Path(transcript_path)
        if not transcript_file.exists():
            raise FileNotFoundError(f"Transcript file not found: {transcript_file}")
    else:
        fetched_path = fetch_latest_transcript(symbol, api_key=transcript_api_key)
        if not fetched_path:
            raise TranscriptPipelineError(
                f"Unable to fetch transcript for symbol {symbol}. Check ticker and API credentials."
            )
        transcript_file = Path(fetched_path)

    summary = synthesize_transcript(
        transcript_file,
        company=company,
        model=model,
        client=client,
        max_output_tokens=max_output_tokens,
        extra_instructions=extra_instructions,
        transcript_text_override=transcript_text_override,
    )

    message = build_email(
        subject=subject or f"{company} earnings call summary ({symbol})",
        sender=sender,
        recipients=recipients,
        summary_text=summary.summary_text,
        transcript_path=summary.transcript_path,
    )

    send_email(
        message,
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        username=smtp_username,
        password=smtp_password,
        use_tls=use_tls,
    )

    return summary
