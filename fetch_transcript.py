"""Fetch the most recent earnings call transcript for a given symbol using RapidAPI Seeking Alpha."""

import os
import requests
from datetime import datetime
from typing import Optional

# API Configuration
HOST = "seeking-alpha.p.rapidapi.com"


def get_transcript_article_id(symbol: str, api_key: Optional[str] = None) -> Optional[str]:
    """
    Get the article ID for the most recent transcript for a given symbol.
    
    Args:
        symbol: Stock ticker symbol (e.g., "UPST", "AAPL")
        api_key: RapidAPI key. If not provided, will try to get from environment variable RAPIDAPI_KEY
    
    Returns:
        str: Article ID if found, None otherwise
    """
    # Get API key from parameter or environment variable
    if api_key is None:
        api_key = os.getenv("RAPIDAPI_KEY")
        if not api_key:
            raise ValueError(
                "RapidAPI key is required. Set it as RAPIDAPI_KEY environment variable "
                "or pass it as api_key parameter."
            )
    
    url = f"https://{HOST}/news/v2/list-by-symbol"
    
    # Try different parameter formats - some APIs are case-sensitive or need different formats
    params = {
        "symbol": symbol.upper()
    }
    
    # Alternative: try with lowercase or as-is
    # params = {"symbol": symbol}  # Uncomment to try without uppercase
    
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": HOST
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        # Debug: Print request details
        print(f"Request URL: {response.url}")
        print(f"Response Status: {response.status_code}")
        
        # Handle 204 No Content - valid response but no data
        if response.status_code == 204:
            print(f"No articles found for symbol {symbol} (204 No Content)")
            print("This could mean:")
            print("  - The symbol has no articles available")
            print("  - The endpoint or parameters might need adjustment")
            print("  - Try checking the RapidAPI documentation for the correct endpoint format")
            return None
        
        # Handle HTTP errors
        if response.status_code == 404:
            print(f"No articles found for symbol {symbol}")
            if response.text:
                print(f"Response text: {response.text[:200]}")
            return None
        elif response.status_code == 401:
            print("Authentication failed. Please check your RapidAPI key.")
            if response.text:
                print(f"Response text: {response.text[:200]}")
            return None
        elif response.status_code == 403:
            print("Access forbidden. Check your API subscription/plan.")
            if response.text:
                print(f"Response text: {response.text[:200]}")
            return None
        elif response.status_code >= 400:
            print(f"API error: {response.status_code}")
            if response.text:
                print(f"Response: {response.text[:500]}")
            return None
        
        response.raise_for_status()
        
        # Check if response is empty (but not 204, which we already handled)
        if not response.text or not response.text.strip():
            print(f"Empty response from API (status: {response.status_code})")
            print(f"Response headers: {dict(response.headers)}")
            print(f"Content-Type: {response.headers.get('Content-Type', 'Not set')}")
            print(f"Content-Length: {response.headers.get('Content-Length', 'Not set')}")
            return None
        
        # Try to parse JSON
        try:
            resp = response.json()
        except ValueError as json_error:
            print(f"Failed to parse JSON response: {json_error}")
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            print(f"Response text (first 500 chars): {response.text[:500]}")
            return None
        
        # Debug: Print response structure
        print(f"Response keys: {list(resp.keys()) if isinstance(resp, dict) else 'Not a dict'}")
        if isinstance(resp, dict) and "data" in resp:
            print(f"Number of articles found: {len(resp.get('data', []))}")
        
        # Search for transcript in the articles
        data_items = resp.get("data", [])
        if not data_items:
            print(f"No articles found in response for symbol {symbol}")
            print(f"Full response structure: {resp}")
            return None
        
        for item in data_items:
            # Check if this is a transcript article
            attributes = item.get("attributes", {})
            title = attributes.get("title", "").lower()
            if "transcript" in title:
                article_id = item.get("id")
                if article_id:
                    print(f"Found transcript article ID: {article_id}")
                    return article_id
        
        print(f"No transcript found in articles for symbol {symbol}")
        return None
        
    except requests.exceptions.Timeout:
        print("Request timed out. Please try again.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching article list from API: {e}")
        return None
    except (KeyError, TypeError) as e:
        print(f"Unexpected response format: {e}")
        return None


def get_earnings_transcript(article_id: str, api_key: Optional[str] = None) -> Optional[dict]:
    """
    Fetch earnings transcript using the article ID from the Seeking Alpha API via RapidAPI.
    
    Args:
        article_id: Article ID obtained from get_transcript_article_id()
        api_key: RapidAPI key. If not provided, will try to get from environment variable RAPIDAPI_KEY
    
    Returns:
        dict: JSON response from the API, or None if not found or error occurred
    """
    # Get API key from parameter or environment variable
    if api_key is None:
        api_key = os.getenv("RAPIDAPI_KEY")
        if not api_key:
            raise ValueError(
                "RapidAPI key is required. Set it as RAPIDAPI_KEY environment variable "
                "or pass it as api_key parameter."
            )
    
    url = f"https://{HOST}/transcripts/get-transcript"
    
    params = {
        "id": article_id
    }
    
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": HOST
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        # Handle 404 gracefully - transcript not found
        if response.status_code == 404:
            print(f"No transcript found for article ID {article_id}")
            return None
        
        # Handle other HTTP errors
        if response.status_code == 401:
            print("Authentication failed. Please check your RapidAPI key.")
            return None
        elif response.status_code == 403:
            print("Access forbidden. Check your API subscription/plan.")
            return None
        elif response.status_code >= 400:
            print(f"API error: {response.status_code} - {response.text[:200]}")
            return None
        
        response.raise_for_status()  # Raise for other unexpected errors
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
        
        # Step 1: Get the transcript article ID
        print(f"Step 1: Finding transcript article ID for {symbol}...")
        article_id = get_transcript_article_id(symbol, api_key)
        
        if article_id is None:
            print(f"Could not find transcript article ID for {symbol}")
            return None
        
        # Step 2: Fetch the transcript using the article ID
        print(f"Step 2: Fetching transcript using article ID {article_id}...")
        data = get_earnings_transcript(article_id, api_key)
        
        # Check if we got valid data
        if data is None:
            print(f"Could not fetch transcript for article ID {article_id}")
            return None
        
        # Extract transcript content
        # The API response structure may vary, so we'll handle different formats
        transcript_content = None
        
        if isinstance(data, dict):
            # Try common field names for transcript content
            if "transcript" in data:
                transcript_content = data["transcript"]
            elif "content" in data:
                transcript_content = data["content"]
            elif "text" in data:
                transcript_content = data["text"]
            elif "data" in data and isinstance(data["data"], dict):
                # Nested data structure
                if "transcript" in data["data"]:
                    transcript_content = data["data"]["transcript"]
                elif "content" in data["data"]:
                    transcript_content = data["data"]["content"]
            else:
                # If we can't find transcript content, save the whole response as JSON
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
