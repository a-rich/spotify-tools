"""Tests for the search module."""

from unittest.mock import MagicMock

import pytest

from spotify_tools.schemas import Track, Artist
from spotify_tools.search import (
    SearchResult,
    search_tracks,
    search_track,
    search_track_fuzzy,
    filter_tracks_by_similarity,
    calculate_similarity,
    is_duplicate_track,
)


@pytest.fixture
def mock_client():
    """Create a mock Spotify client."""
    return MagicMock()


@pytest.fixture
def sample_tracks():
    """Create sample Track objects for testing."""
    return [
        Track(
            id="track1",
            name="Test Song",
            uri="spotify:track:track1",
            artists=[Artist(name="Test Artist")],
        ),
        Track(
            id="track2",
            name="Another Song",
            uri="spotify:track:track2",
            artists=[Artist(name="Another Artist")],
        ),
        Track(
            id="track3",
            name="Test Song Remix",
            uri="spotify:track:track3",
            artists=[Artist(name="Test Artist"), Artist(name="DJ Remix")],
        ),
    ]


def test_search_tracks_returns_results(mock_client, sample_tracks):
    """Test that search_tracks returns Track objects."""
    mock_client.search.return_value = {
        "tracks": {
            "items": [t.model_dump() for t in sample_tracks],
            "href": "http://example.com",
            "limit": 50,
            "next": None,
            "offset": 0,
            "total": 3,
        }
    }

    results = search_tracks(mock_client, "test query")

    assert len(results) == 3
    assert results[0].name == "Test Song"
    mock_client.search.assert_called_once_with(
        q="test query", limit=50, type="track"
    )


def test_search_tracks_handles_empty_results(mock_client):
    """Test that search_tracks handles empty results gracefully."""
    mock_client.search.return_value = {"tracks": {"items": []}}

    results = search_tracks(mock_client, "nonexistent")

    assert results == []


def test_search_tracks_handles_exception(mock_client):
    """Test that search_tracks handles exceptions gracefully."""
    mock_client.search.side_effect = Exception("API Error")

    results = search_tracks(mock_client, "test")

    assert results == []


def test_search_track_with_artist(mock_client, sample_tracks):
    """Test search_track with artist parameter."""
    mock_client.search.return_value = {
        "tracks": {
            "items": [sample_tracks[0].model_dump()],
            "href": "http://example.com",
            "limit": 50,
            "next": None,
            "offset": 0,
            "total": 1,
        }
    }

    results = search_track(mock_client, "Test Song", "Test Artist")

    mock_client.search.assert_called_once_with(
        q="track:Test Song artist:Test Artist", limit=50, type="track"
    )
    assert len(results) == 1


def test_filter_tracks_by_similarity(sample_tracks):
    """Test filtering tracks by similarity threshold."""
    # Search for "Test Song" by "Test Artist"
    results = filter_tracks_by_similarity(
        sample_tracks, "Test Song", "Test Artist", threshold=70.0
    )

    # Should match the first track exactly
    assert len(results) >= 1
    assert any(r.track.id == "track1" for r in results)


def test_filter_tracks_by_similarity_no_matches(sample_tracks):
    """Test that filter returns empty list when no matches."""
    results = filter_tracks_by_similarity(
        sample_tracks, "Completely Different", "Unknown Artist", threshold=90.0
    )

    assert results == []


def test_filter_tracks_by_similarity_handles_none_artist(sample_tracks):
    """Test filtering works without artist."""
    results = filter_tracks_by_similarity(
        sample_tracks, "Test Song", None, threshold=70.0
    )

    # Should still find matches based on title
    assert len(results) >= 1


def test_search_track_fuzzy(mock_client, sample_tracks):
    """Test fuzzy search returns best match."""
    mock_client.search.return_value = {
        "tracks": {
            "items": [t.model_dump() for t in sample_tracks],
            "href": "http://example.com",
            "limit": 50,
            "next": None,
            "offset": 0,
            "total": 3,
        }
    }

    result = search_track_fuzzy(
        mock_client, "Test Song", "Test Artist", threshold=70.0
    )

    assert result is not None
    assert isinstance(result, SearchResult)
    assert result.track.name == "Test Song"


def test_search_track_fuzzy_no_match(mock_client):
    """Test fuzzy search returns None when no match."""
    mock_client.search.return_value = {
        "tracks": {"items": [], "next": None, "total": 0}
    }

    result = search_track_fuzzy(
        mock_client, "Nonexistent", "Unknown", threshold=90.0
    )

    assert result is None


def test_search_track_fuzzy_ambiguous_order(mock_client, sample_tracks):
    """Test fuzzy search with ambiguous order tries both."""
    mock_client.search.return_value = {
        "tracks": {
            "items": [sample_tracks[0].model_dump()],
            "href": "http://example.com",
            "limit": 50,
            "next": None,
            "offset": 0,
            "total": 1,
        }
    }

    search_track_fuzzy(
        mock_client,
        "Test Artist",  # Swapped
        "Test Song",  # Swapped
        threshold=70.0,
        ambiguous_order=True,
    )

    # Should have searched twice (normal and swapped)
    assert mock_client.search.call_count == 2


def test_calculate_similarity():
    """Test similarity calculation."""
    # Identical strings
    assert calculate_similarity("hello", "hello") == 100

    # Different strings
    assert calculate_similarity("hello", "world") < 50

    # Case insensitive
    assert calculate_similarity("HELLO", "hello") == 100

    # Similar strings
    assert calculate_similarity("hello", "helo") > 80


def test_is_duplicate_track():
    """Test duplicate detection."""
    existing = {"Test Song - Test Artist", "Another Song - Another Artist"}

    # Exact match
    assert is_duplicate_track("Test Song - Test Artist", existing)

    # Very similar
    assert is_duplicate_track("Test Song - Test Artists", existing, threshold=90)

    # Not similar enough
    assert not is_duplicate_track(
        "Completely Different - Unknown", existing, threshold=90
    )


def test_is_duplicate_track_case_insensitive():
    """Test that duplicate detection is case insensitive."""
    existing = {"Test Song - Test Artist"}

    assert is_duplicate_track("TEST SONG - TEST ARTIST", existing)
    assert is_duplicate_track("test song - test artist", existing)

