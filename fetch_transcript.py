"""Fetch the most recent earnings call transcript for a given symbol using RapidAPI Seeking Alpha."""

import os
import requests
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Configuration
HOST = "seeking-alpha.p.rapidapi.com"


def get_latest_transcript_id(symbol: str, api_key: Optional[str] = None) -> Optional[str]:
    """
    Get the most recent transcript ID for a given symbol using /transcripts/v2/list.
    """
    if api_key is None:
        api_key = os.getenv("RAPIDAPI_KEY")
        if not api_key:
            raise ValueError(
                "RapidAPI key is required. Set it as RAPIDAPI_KEY environment variable "
                "or pass it as api_key parameter."
            )

    url = f"https://{HOST}/transcripts/v2/list"
    params = {"id": symbol.lower(), "size": 1, "number": 1}
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": HOST,
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)

        if response.status_code == 204:
            print(f"No transcripts found for symbol {symbol} (204 No Content)")
            return None
        if response.status_code == 404:
            print(f"No transcripts found for symbol {symbol}")
            return None
        if response.status_code == 401:
            print("Authentication failed. Please check your RapidAPI key.")
            return None
        if response.status_code == 403:
            print("Access forbidden. Check your API subscription/plan.")
            return None
        if response.status_code >= 400:
            print(f"API error: {response.status_code}")
            if response.text:
                print(f"Response: {response.text[:500]}")
            return None

        resp = response.json()
        data_items = resp.get("data", [])
        if not data_items:
            print(f"No transcript items returned for symbol {symbol}")
            return None

        first_item = data_items[0]
        transcript_id = first_item.get("id")
        if not transcript_id:
            print(f"Transcript ID missing in response item: {first_item}")
            return None

        print(f"Found transcript ID: {transcript_id}")
        return transcript_id

    except requests.exceptions.Timeout:
        print("Request timed out. Please try again.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching transcript list from API: {e}")
        return None


def get_earnings_transcript(transcript_id: str, api_key: Optional[str] = None) -> Optional[dict]:
    """
    Fetch earnings transcript details using /transcripts/v2/get-details.
    """
    if api_key is None:
        api_key = os.getenv("RAPIDAPI_KEY")
        if not api_key:
            raise ValueError(
                "RapidAPI key is required. Set it as RAPIDAPI_KEY environment variable "
                "or pass it as api_key parameter."
            )

    url = f"https://{HOST}/transcripts/v2/get-details"
    params = {"id": transcript_id}
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": HOST,
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)

        if response.status_code == 404:
            print(f"No transcript found for ID {transcript_id}")
            return None
        if response.status_code == 401:
            print("Authentication failed. Please check your RapidAPI key.")
            return None
        if response.status_code == 403:
            print("Access forbidden. Check your API subscription/plan.")
            return None
        if response.status_code >= 400:
            print(f"API error: {response.status_code} - {response.text[:200]}")
            return None

        return response.json()

    except requests.exceptions.Timeout:
        print("Request timed out. Please try again.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching transcript from API: {e}")
        return None


def fetch_latest_transcript(symbol: str = "UPST", api_key: Optional[str] = None) -> Optional[str]:
    """
    Fetch the most recent earnings call transcript for a given symbol and save it to a file.
    
    Args:
        symbol: Stock ticker symbol (default: "UPST")
        api_key: RapidAPI key. If not provided, will try to get from environment variable RAPIDAPI_KEY
    
    Returns:
        str: Path to the saved transcript file, or None if failed
    """
    try:
        print(f"Fetching earnings transcript for {symbol}...")
        
        # Step 1: Get the latest transcript ID
        print(f"Step 1: Finding transcript ID for {symbol}...")
        transcript_id = get_latest_transcript_id(symbol, api_key)
        
        if transcript_id is None:
            print(f"Could not find transcript ID for {symbol}")
            return None
        
        # Step 2: Fetch the transcript using the transcript ID
        print(f"Step 2: Fetching transcript using ID {transcript_id}...")
        data = get_earnings_transcript(transcript_id, api_key)
        
        # Check if we got valid data
        if data is None:
            print(f"Could not fetch transcript for ID {transcript_id}")
            return None
        
        # Extract transcript content
        # The API response structure may vary, so we'll handle different formats
        transcript_content = None
        
        if isinstance(data, dict):
            if "data" in data and isinstance(data["data"], dict):
                attributes = data["data"].get("attributes", {})
                transcript_content = (
                    attributes.get("content")
                    or attributes.get("transcript")
                    or data["data"].get("content")
                )
            # Try top-level fallbacks
            if not transcript_content:
                if "transcript" in data:
                    transcript_content = data["transcript"]
                elif "content" in data:
                    transcript_content = data["content"]
                elif "text" in data:
                    transcript_content = data["text"]
            if not transcript_content:
                import json
                transcript_content = json.dumps(data, indent=2)
        elif isinstance(data, str):
            transcript_content = data
        else:
            # Convert to string if it's something else
            import json
            transcript_content = json.dumps(data, indent=2)
        
        if not transcript_content:
            print(f"Could not extract transcript content from API response")
            print(f"Response structure: {list(data.keys()) if isinstance(data, dict) else type(data)}")
            return None
        
        # Extract date information if available for filename
        date_str = None
        if isinstance(data, dict):
            if "data" in data and isinstance(data["data"], dict):
                attributes = data["data"].get("attributes", {})
                date_str = (
                    attributes.get("publishDate")
                    or attributes.get("publishOn")
                    or attributes.get("date")
                )
            if not date_str:
                if "date" in data:
                    date_str = data["date"]
                elif "earnings_date" in data:
                    date_str = data["earnings_date"]
                elif "published_date" in data:
                    date_str = data["published_date"]
                elif "data" in data and isinstance(data["data"], dict):
                    if "date" in data["data"]:
                        date_str = data["data"]["date"]
        
        # Create transcripts directory if it doesn't exist
        transcripts_dir = "transcripts"
        os.makedirs(transcripts_dir, exist_ok=True)
        
        # Generate filename
        if date_str:
            try:
                # Try to parse and format the date
                if isinstance(date_str, str):
                    # Try common date formats
                    for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y', '%Y-%m-%dT%H:%M:%S']:
                        try:
                            date_obj = datetime.strptime(date_str.split('T')[0], fmt)
                            date_str = date_obj.strftime('%Y-%m-%d')
                            break
                        except ValueError:
                            continue
                filename = f"{symbol}_{date_str}_transcript.txt"
            except Exception:
                filename = f"{symbol}_transcript.txt"
        else:
            # Use current date if no date in response
            current_date = datetime.now().strftime('%Y-%m-%d')
            filename = f"{symbol}_{current_date}_transcript.txt"
        
        file_path = os.path.join(transcripts_dir, filename)
        
        # Save transcript to file
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(str(transcript_content))
        
        print(f"Transcript saved to {file_path}")
        return file_path
        
    except ValueError as e:
        print(f"Configuration error: {e}")
        return None
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    fetch_latest_transcript("AAPL")
