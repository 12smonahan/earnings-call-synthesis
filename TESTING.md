# Testing Guide

This guide explains how to test the earnings call synthesis codebase.

## Quick Start

Run the manual test script:

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all tests
python tests/test_manual.py

# Or run individual tests
python tests/test_manual.py env      # Check environment variables
python tests/test_manual.py fetch    # Test transcript fetching
python tests/test_manual.py summarize # Test summarization
python tests/test_manual.py email    # Test email building
```

## Prerequisites

1. **Set up environment variables** in `.env`:
   ```bash
   OPENAI_API_KEY=your-openai-key
   RAPIDAPI_KEY=your-rapidapi-key
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Testing Individual Components

### 1. Test Transcript Fetching

```bash
python -c "from earnings_call.transcripts import fetch_latest_transcript; fetch_latest_transcript('UPST')"
```

This will:
- Fetch the latest transcript for UPST
- Save it to `transcripts/` directory
- Print the file path on success

**Expected output:**
```
Fetching earnings transcript for UPST...
Step 1: Finding transcript ID for UPST...
Found transcript ID: <id>
Step 2: Fetching transcript using ID <id>...
Transcript saved to transcripts/UPST_YYYY-MM-DD_transcript.txt
```

### 2. Test Summarizer

```python
from pathlib import Path
from earnings_call.summarizer import synthesize_transcript

# Use an existing transcript
summary = synthesize_transcript(
    Path("transcripts/UPST_2025-10-30_transcript.txt"),
    company="Upstart",
    model="gpt-4o-mini",
    max_output_tokens=400
)

print(summary.summary_text)
```

**Expected:** A structured summary with sections like:
- Economic performance
- Credit performance
- Macro & consumer health
- New products/partnerships
- Risks & watch-outs

### 3. Test Email Builder

```python
from earnings_call.emailer import build_email
from pathlib import Path

message = build_email(
    subject="Test Summary",
    sender="test@example.com",
    recipients=["recipient@example.com"],
    summary_text="Test summary text",
    transcript_path=Path("transcripts/UPST_2025-10-30_transcript.txt"),
    company="Upstart Holdings",
    symbol="UPST",
)

print(f"Subject: {message['Subject']}")
print(f"To: {message['To']}")
```

**Note:** This builds the email but doesn't send it. To actually send, you need SMTP credentials.

### 4. Test End-to-End Pipeline

```python
from earnings_call.pipeline import generate_and_email_transcript

# This will fetch, summarize, and email (if SMTP is configured)
summary = generate_and_email_transcript(
    symbol="UPST",
    company="Upstart",
    sender="your-email@example.com",
    recipients=["recipient@example.com"],
    smtp_host="smtp.example.com",
    smtp_username="smtp-user",
    smtp_password="smtp-pass",
)
```

## Testing with Mock Data

For testing without API calls, you can use the `transcript_text_override` parameter:

```python
from earnings_call.summarizer import synthesize_transcript
from pathlib import Path

# Test with mock transcript text
mock_transcript = """
Operator: Welcome to the earnings call...
CEO: Thank you. This quarter we saw strong growth...
"""

summary = synthesize_transcript(
    Path("mock.txt"),  # Path doesn't need to exist
    company="Test Corp",
    transcript_text_override=mock_transcript
)
```

## Automated Testing (Optional)

To set up pytest for automated testing:

```bash
# Add pytest to dev dependencies
pip install pytest pytest-mock

# Create tests directory
mkdir tests

# Create test file
cat > tests/test_summarizer.py << 'EOF'
import pytest
from pathlib import Path
from earnings_call.summarizer import synthesize_transcript

def test_summarizer_with_mock_text():
    mock_text = "This is a test transcript about earnings."
    summary = synthesize_transcript(
        Path("test.txt"),
        company="Test Corp",
        transcript_text_override=mock_text
    )
    assert summary.company == "Test Corp"
    assert len(summary.summary_text) > 0
EOF

# Run tests
pytest tests/
```

## Troubleshooting

### "OPENAI_API_KEY not set"
- Check your `.env` file exists and has the key
- Verify it's loaded: `python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('OPENAI_API_KEY'))"`

### "RAPIDAPI_KEY not set"
- Same as above, check `.env` file
- Verify the key is valid in RapidAPI dashboard

### "No transcript files found"
- Run the fetch test first to download a transcript
- Or manually add a transcript file to `transcripts/` directory

### "Failed to fetch transcript"
- Check your RapidAPI subscription includes the Seeking Alpha API
- Verify the symbol is correct (e.g., "UPST" not "upstart")
- Check API rate limits

### "Failed to generate summary"
- Verify your OpenAI API key is valid
- Check you have credits/quota available
- Try a shorter transcript or reduce `max_output_tokens`

## Integration Testing

Test the full pipeline with the provided script:

```bash
# Set all required environment variables
export OPENAI_API_KEY=your-key
export RAPIDAPI_KEY=your-key
export SENDER_EMAIL=your-email@example.com
export SMTP_HOST=smtp.example.com
export SMTP_USERNAME=smtp-user
export SMTP_PASSWORD=smtp-pass

# Run the pipeline script (configured for UPST)
python scripts/send_latest_aapl.py
```

This will:
1. Fetch latest UPST transcript
2. Generate summary
3. Email both to the recipient

