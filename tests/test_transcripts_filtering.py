"""Unit tests for transcript filtering logic."""

from earnings_call.transcripts import _select_transcript_id


def test_select_transcript_id_skips_slide_decks():
    data_items = [
        {
            "id": "111",
            "attributes": {
                "title": "Upstart Holdings Q3 2025 Earnings Call Slide Deck",
                "contentType": "slideshow",
            },
        },
        {
            "id": "222",
            "attributes": {
                "title": "Upstart Holdings Q3 2025 Earnings Call Transcript",
                "contentType": "transcript",
            },
        },
    ]

    assert _select_transcript_id(data_items) == "222"


def test_select_transcript_id_returns_none_when_no_transcript_like_items():
    data_items = [
        {
            "id": "333",
            "attributes": {
                "title": "Company Overview Presentation",
                "contentType": "article",
            },
        }
    ]

    assert _select_transcript_id(data_items) is None
