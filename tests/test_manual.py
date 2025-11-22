"""Manual end-to-end test for the earnings call synthesis pipeline.

This script exercises the real transcript fetch, summarization, and email
assembly workflow for Upstart (UPST). Configure OPENAI_API_KEY and
RAPIDAPI_KEY in your .env file so it can hit the live services.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Add src directory to Python path so we can import earnings_call when running directly
project_root = Path(__file__).resolve().parents[1]
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Load environment variables
load_dotenv()


DEFAULT_SYMBOL = "UPST"
DEFAULT_COMPANY = "Upstart Holdings"


def test_fetch_transcript():
    """Test fetching a transcript."""
    print("\n" + "=" * 60)
    print("TEST 1: Fetch Transcript")
    print("=" * 60)
    
    from earnings_call.transcripts import fetch_latest_transcript
    
    symbol = DEFAULT_SYMBOL
    print(f"Fetching transcript for {symbol}...")
    
    result = fetch_latest_transcript(symbol)
    
    if result:
        print(f"✓ Success! Transcript saved to: {result}")
        return True
    else:
        print("✗ Failed to fetch transcript")
        return False


def test_summarizer():
    """Test the summarizer with an existing transcript."""
    print("\n" + "=" * 60)
    print("TEST 2: Summarize Transcript")
    print("=" * 60)
    
    # Check if we have a transcript file
    transcript_dir = Path("transcripts")
    transcript_files = list(transcript_dir.glob("*.txt"))

    if not transcript_files:
        print("No transcript found locally; fetching latest before summarizing...")
        try:
            from earnings_call.transcripts import fetch_latest_transcript

            fetch_result = fetch_latest_transcript(DEFAULT_SYMBOL)
            if not fetch_result:
                print("✗ Failed to fetch transcript for summarization")
                return False
            transcript_files = [Path(fetch_result)]
        except Exception as e:
            print(f"✗ Could not fetch transcript automatically: {e}")
            return False

    # Use the most recently modified transcript
    transcript_path = max(transcript_files, key=lambda p: p.stat().st_mtime)
    print(f"Using transcript: {transcript_path}")
    
    from earnings_call.summarizer import synthesize_transcript
    
    try:
        summary = synthesize_transcript(
            transcript_path,
            company=DEFAULT_COMPANY,
            model="gpt-4o-mini",
            max_output_tokens=400,  # Shorter for testing
        )
        
        print(f"✓ Success! Summary generated ({len(summary.summary_text)} characters)")
        print("\nSummary preview (first 200 chars):")
        print("-" * 60)
        print(summary.summary_text[:200] + "...")
        print("-" * 60)
        return True
    except Exception as e:
        print(f"✗ Failed to generate summary: {e}")
        return False


def test_email_builder():
    """Test building and sending an email to 12smonahan@gmail.com."""
    print("\n" + "=" * 60)
    print("TEST 3: Send Email")
    print("=" * 60)
    
    transcript_dir = Path("transcripts")
    transcript_files = list(transcript_dir.glob("*.txt"))
    
    if not transcript_files:
        print("✗ No transcript files found")
        return False
    
    transcript_path = transcript_files[0]
    
    # Check for SMTP configuration
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    use_tls = os.getenv("SMTP_USE_TLS", "true").strip().lower() not in {"0", "false", "no", "off"}
    
    if not smtp_host:
        print("⚠️  SMTP_HOST not set - skipping email send test")
        print("   Set SMTP_HOST, SMTP_USERNAME, and SMTP_PASSWORD to test email sending")
        return None
    
    # Try to get a real summary if we have OpenAI key, otherwise use a fallback summary
    summary_text = None
    if os.getenv("OPENAI_API_KEY"):
        try:
            from earnings_call.summarizer import synthesize_transcript
            summary = synthesize_transcript(
                transcript_path,
                company=DEFAULT_COMPANY,
                model="gpt-4o-mini",
                max_output_tokens=400,
            )
            summary_text = summary.summary_text
            print(f"Generated summary using OpenAI ({len(summary_text)} chars)")
        except Exception as e:
            print(f"Could not generate summary: {e}")
            print("Using test summary instead")

    if not summary_text:
        summary_text = (
            "Automated summary of the latest Upstart Holdings earnings call."
        )
    
    from earnings_call.emailer import build_email, send_email
    
    email_address = "12smonahan@gmail.com"
    
    try:
        # Build the email
        message = build_email(
            subject="Upstart Holdings Earnings Call Summary",
            sender=email_address,
            recipients=[email_address],
            summary_text=summary_text,
            transcript_path=transcript_path,
        )
        
        print(f"Email built successfully")
        print(f"  Subject: {message['Subject']}")
        print(f"  From: {message['From']}")
        print(f"  To: {message['To']}")
        print(f"  Attachments: {len(message.get_payload()) - 1}")  # -1 for body
        
        # Send the email
        print(f"\nSending email to {email_address}...")
        send_email(
            message,
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            username=smtp_username,
            password=smtp_password,
            use_tls=use_tls,
        )
        
        print(f"✓ Success! Email sent to {email_address}")
        return True
    except Exception as e:
        print(f"✗ Failed to send email: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_environment_variables():
    """Test that required environment variables are set."""
    print("\n" + "=" * 60)
    print("TEST 0: Environment Variables")
    print("=" * 60)
    
    required_vars = {
        "OPENAI_API_KEY": "OpenAI API key for summarization",
        "RAPIDAPI_KEY": "RapidAPI key for transcript fetching",
    }
    
    all_set = True
    for var_name, description in required_vars.items():
        value = os.getenv(var_name)
        if value:
            # Don't print the actual key, just confirm it's set
            masked = value[:8] + "..." if len(value) > 8 else "***"
            print(f"✓ {var_name}: {masked} ({description})")
        else:
            print(f"✗ {var_name}: NOT SET ({description})")
            all_set = False
    
    return all_set


def run_all_tests():
    """Run all tests in sequence."""
    print("\n" + "=" * 60)
    print("RUNNING ALL TESTS")
    print("=" * 60)
    
    results = {}
    
    # Test 0: Environment variables
    results["env_vars"] = test_environment_variables()
    
    if not results["env_vars"]:
        print("\n⚠️  Warning: Some environment variables are missing.")
        print("   Some tests may fail. Set them in your .env file.")
    
    # Test 1: Fetch transcript (requires RAPIDAPI_KEY)
    if os.getenv("RAPIDAPI_KEY"):
        results["fetch"] = test_fetch_transcript()
    else:
        print("\n⚠️  Skipping fetch test (RAPIDAPI_KEY not set)")
        results["fetch"] = None
    
    # Test 2: Summarizer (requires OPENAI_API_KEY and a transcript file)
    if os.getenv("OPENAI_API_KEY"):
        results["summarize"] = test_summarizer()
    else:
        print("\n⚠️  Skipping summarizer test (OPENAI_API_KEY not set)")
        results["summarize"] = None
    
    # Test 3: Email builder/sender (needs SMTP config and transcript file)
    results["email"] = test_email_builder()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result is True else "✗ FAIL" if result is False else "⊘ SKIP"
        print(f"{status}: {test_name}")
    
    passed = sum(1 for r in results.values() if r is True)
    total = sum(1 for r in results.values() if r is not None)
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    return all(results.values())


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        if test_name == "env":
            test_environment_variables()
        elif test_name == "fetch":
            test_fetch_transcript()
        elif test_name == "summarize":
            test_summarizer()
        elif test_name == "email":
            test_email_builder()
        else:
            print(f"Unknown test: {test_name}")
            print("Available tests: env, fetch, summarize, email")
    else:
        run_all_tests()

