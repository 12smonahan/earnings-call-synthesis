# earnings-call-synthesis

Utilities to synthesize earnings call transcripts for competitor monitoring. The summarization
module produces analyst-style readouts using the OpenAI API, and the emailer module sends both the
summary and full transcript to stakeholders. A small pipeline ties together transcript fetching,
summarization, and delivery so you can get the latest call out to recipients in one command.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set the `OPENAI_API_KEY` environment variable so the summarizer can authenticate.
3. Set the `RAPIDAPI_KEY` environment variable to authorize Seeking Alpha transcript requests.
4. Ensure you have access to an SMTP server for sending emails (host, port, username/password if required).

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
Uses Seeking Alpha API to synthesize earnings call transcripts and send email triggers to users

## End-to-end pipeline

Use the pipeline helper when you want to stitch transcript fetching, summarization, and email
delivery together.

```python
from earnings_call.pipeline import generate_and_email_transcript

generate_and_email_transcript(
    symbol="UPST",
    company="Upstart",
    sender="analyst@example.com",
    recipients=["exec1@example.com"],
    smtp_host="smtp.example.com",
    smtp_username="smtp-user",
    smtp_password="smtp-pass",
)
```

Required environment for the above:

* `RAPIDAPI_KEY` – Seeking Alpha API key for `fetch_transcript.py`.
* `OPENAI_API_KEY` – OpenAI key for the summarizer.
* SMTP variables per your server (`SMTP_HOST`, optional `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_USE_TLS`).

The function returns a `TranscriptSummary` so callers can log or reuse the generated summary text.

### Test script for Apple

To email the latest Apple earnings call transcript and summary to `12smonahan@gmail.com`, provide
SMTP credentials and run:

```bash
export SENDER_EMAIL="analyst@example.com"
export SMTP_HOST="smtp.example.com"
export SMTP_USERNAME="user"
export SMTP_PASSWORD="pass"
export RAPIDAPI_KEY="<rapidapi-key>"
export OPENAI_API_KEY="<openai-key>"

python scripts/send_latest_aapl.py
```

Use `RECIPIENT_EMAIL` to override the default destination, and `SMTP_PORT`/`SMTP_USE_TLS` to adjust
mail transport settings.

## Setup

This project uses Python 3.12 and Poetry for dependency management.

### Prerequisites

1. **Install Python 3.12**
   - On macOS: `brew install python@3.12` (requires Homebrew)
   - Or download from [python.org](https://www.python.org/downloads/)
   - Or use pyenv: `pyenv install 3.12`

2. **Install Poetry** (if not already installed)
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```
   Add Poetry to your PATH:
   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   ```

### Creating the Virtual Environment

Once Python 3.12 is installed, create the virtual environment:

```bash
# Make sure Poetry is in your PATH
export PATH="$HOME/.local/bin:$PATH"

# Create virtual environment with Python 3.12
poetry env use python3.12

# Install dependencies (when you add them)
poetry install
```

The virtual environment will be created in `.venv/` directory within the project (configured via Poetry settings).

### Using the Virtual Environment

```bash
# Activate the environment
poetry shell

# Or run commands within the environment
poetry run python <script>
```
