# earnings-call-synthesis

Utilities to synthesize earnings call transcripts for competitor monitoring. The summarization
module produces analyst-style readouts using the OpenAI API, and the emailer module sends both the
summary and full transcript to stakeholders.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set the `OPENAI_API_KEY` environment variable so the summarizer can authenticate.
3. Ensure you have access to an SMTP server for sending emails (host, port, username/password if required).

## Generating a summary

```python
from pathlib import Path
from earnings_call.summarizer import synthesize_transcript

summary = synthesize_transcript(
    Path("./transcripts/acme_q2.txt"),
    company="ACME Lending",
)
print(summary.summary_text)
```

You can provide optional `extra_instructions` to highlight custom angles and adjust the OpenAI
`model`, `max_output_tokens`, or supply a shared `client` instance.

The summarizer will raise a `FileNotFoundError` if the transcript path is missing and a
`ValueError` if provided content is empty, ensuring you catch data issues early.

## Emailing the summary and transcript

```python
from earnings_call.emailer import build_email, send_email

message = build_email(
    subject="ACME Q2 earnings readout",
    sender="analyst@example.com",
    recipients=["exec1@example.com", "exec2@example.com"],
    summary_text=summary.summary_text,
    transcript_path=summary.transcript_path,
)

send_email(
    message,
    smtp_host="smtp.example.com",
    smtp_port=587,
    username="smtp-user",
    password="smtp-password",
)
```

The `build_email` helper attaches the plain-text transcript and uses your summary as the message
body, allowing recipients to skim quickly and drill into the source material.

If you pass an empty recipient list or a missing transcript file, `build_email` will raise
an explicit error to help you surface configuration problems before attempting delivery.
