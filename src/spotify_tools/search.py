"""Search functionality for finding tracks on Spotify."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

from fuzzywuzzy import fuzz

from spotify_tools.logging import get_logger
from spotify_tools.schemas import Track, TrackSearchResults


logger = get_logger(__name__)


class SearchType(Enum):
    """Spotify search types."""

    ALBUM = "album"
    ARTIST = "artist"
    EPISODE = "episode"
    PLAYLIST = "playlist"
    SHOW = "show"
    TRACK = "track"


@dataclass
class SearchResult:
    """Result of a search operation with match score."""

    track: Track
    score: float


def search_tracks(
    client,
    query: str,
    limit: int = 50,
) -> list[Track]:
    """Search for tracks using a raw query string.

    Args:
        client: Spotify client.
        query: Raw Spotify search query (e.g. "track:Title artist:Artist").
        limit: Maximum number of results to return.

    Returns:
        List of matching Track objects.
    """
    try:
        results = client.search(q=query, limit=limit, type="track")
    except Exception as exc:
        logger.warning(f"Search failed for query '{query}': {exc}")
        return []

    if not results or "tracks" not in results:
        return []

    track_results = TrackSearchResults.model_validate(results["tracks"])
    return track_results.items or []


def search_track(
    client,
    title: str,
    artist: Optional[str] = None,
    limit: int = 50,
) -> list[Track]:
    """Search for tracks by title and optionally artist.

    Args:
        client: Spotify client.
        title: Track title to search for.
        artist: Optional artist name to narrow results.
        limit: Maximum number of results to return.

    Returns:
        List of matching Track objects.
    """
    query = f"track:{title}"
    if artist:
        query += f" artist:{artist}"

    return search_tracks(client, query, limit)


def search_track_fuzzy(
    client,
    title: str,
    artist: Optional[str] = None,
    threshold: float = 70.0,
    limit: int = 50,
    ambiguous_order: bool = False,
) -> Optional[SearchResult]:
    """Search for a track with fuzzy matching on title and artist.

    This function searches Spotify for tracks matching the given title/artist,
    then applies fuzzy string matching to find the best match above the
    threshold.

    Args:
        client: Spotify client.
        title: Track title to search for.
        artist: Optional artist name.
        threshold: Minimum similarity score (0-100) for a match.
        limit: Maximum number of search results to consider.
        ambiguous_order: If True, also searches with title/artist swapped.

    Returns:
        SearchResult with best matching track and score, or None if no match.
    """
    queries = [(title, artist)]
    if ambiguous_order and artist:
        queries.append((artist, title))

    all_matches: list[SearchResult] = []

    for track_query, artist_query in queries:
        tracks = search_track(client, track_query, artist_query, limit)
        matches = filter_tracks_by_similarity(
            tracks, title, artist, threshold
        )
        all_matches.extend(matches)

        # Also paginate through results if there are more
        # (handled by search_track_with_pagination for more thorough search)

    if not all_matches:
        return None

    # Return the best match
    return max(all_matches, key=lambda m: m.score)


def search_track_with_pagination(
    client,
    title: str,
    artist: Optional[str] = None,
    threshold: float = 70.0,
    limit: int = 50,
    ambiguous_order: bool = False,
) -> Optional[SearchResult]:
    """Search for a track with pagination through all results.

    Similar to search_track_fuzzy but paginates through all available
    results from Spotify to find the best match.

    Args:
        client: Spotify client.
        title: Track title to search for.
        artist: Optional artist name.
        threshold: Minimum similarity score (0-100) for a match.
        limit: Results per page.
        ambiguous_order: If True, also searches with title/artist swapped.

    Returns:
        SearchResult with best matching track and score, or None if no match.
    """
    queries = [(title, artist)]
    if ambiguous_order and artist:
        queries.append((artist, title))

    all_matches: list[SearchResult] = []

    for track_query, artist_query in queries:
        query = f"track:{track_query}"
        if artist_query:
            query += f" artist:{artist_query}"

        try:
            results = client.search(q=query, limit=limit, type="track")
        except Exception as exc:
            logger.warning(f"Search failed for '{track_query}': {exc}")
            continue

        if not results or "tracks" not in results:
            continue

        # Process first page
        track_results = TrackSearchResults.model_validate(results["tracks"])
        tracks = track_results.items or []
        matches = filter_tracks_by_similarity(tracks, title, artist, threshold)
        all_matches.extend(matches)

        # Paginate through remaining results
        while track_results.next:
            try:
                next_results = client.next(results["tracks"])
                if not next_results:
                    break
                track_results = TrackSearchResults.model_validate(next_results)
                tracks = track_results.items or []
                matches = filter_tracks_by_similarity(
                    tracks, title, artist, threshold
                )
                all_matches.extend(matches)
            except Exception as exc:
                logger.warning(f"Failed to get next page: {exc}")
                break

    if not all_matches:
        return None

    return max(all_matches, key=lambda m: m.score)


def filter_tracks_by_similarity(
    tracks: list[Track],
    title: str,
    artist: Optional[str],
    threshold: float,
) -> list[SearchResult]:
    """Filter tracks by fuzzy similarity to title and artist.

    Args:
        tracks: List of tracks to filter.
        title: Expected track title.
        artist: Expected artist name(s).
        threshold: Minimum similarity score (0-100).

    Returns:
        List of SearchResult objects for tracks meeting the threshold.
    """
    results = []
    title_lower = title.lower()
    artist_lower = artist.lower() if artist else ""

    # Normalize artist string (sort comma-separated artists)
    if artist:
        artist_normalized = ", ".join(
            sorted(x.strip() for x in artist_lower.split(","))
        )
    else:
        artist_normalized = ""

    for track in tracks:
        if not track or not track.name:
            continue

        track_name = track.name.lower()

        # Get all artist names from track
        track_artists = ""
        if track.artists:
            track_artists = ", ".join(
                sorted(a.name.lower() for a in track.artists if a.name)
            )

        # Calculate title match (check against both title and artist input
        # in case they're swapped)
        title_match = max(
            fuzz.ratio(track_name, title_lower),
            fuzz.ratio(track_name, artist_lower) if artist_lower else 0,
        )

        # Calculate artist match
        if artist_normalized:
            artist_match = max(
                fuzz.ratio(track_artists, title_lower),
                fuzz.ratio(track_artists, artist_normalized),
            )
        else:
            # If no artist provided, just use title match
            artist_match = title_match

        # Both must meet threshold
        if title_match >= threshold and artist_match >= threshold:
            combined_score = title_match + artist_match
            results.append(SearchResult(track=track, score=combined_score))

    return results


def batch_search_tracks(
    client,
    queries: list[tuple[str, Optional[str]]],
    threshold: float = 70.0,
    limit: int = 50,
    max_workers: int = 8,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> list[Optional[SearchResult]]:
    """Search for multiple tracks in parallel.

    Args:
        client: Spotify client.
        queries: List of (title, artist) tuples to search for.
        threshold: Minimum similarity score (0-100).
        limit: Results per search.
        max_workers: Maximum parallel workers.
        progress_callback: Optional callback(completed, total) for progress.

    Returns:
        List of SearchResult or None for each query, in same order as input.
    """
    results: list[Optional[SearchResult]] = [None] * len(queries)

    def search_one(index: int, title: str, artist: Optional[str]):
        result = search_track_fuzzy(
            client, title, artist, threshold, limit, ambiguous_order=True
        )
        return index, result

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(search_one, i, title, artist)
            for i, (title, artist) in enumerate(queries)
        ]

        completed = 0
        for future in futures:
            try:
                index, result = future.result()
                results[index] = result
            except Exception as exc:
                logger.warning(f"Search failed: {exc}")

            completed += 1
            if progress_callback:
                progress_callback(completed, len(queries))

    return results


def calculate_similarity(str1: str, str2: str) -> float:
    """Calculate fuzzy similarity between two strings.

    Args:
        str1: First string.
        str2: Second string.

    Returns:
        Similarity score from 0-100.
    """
    return fuzz.ratio(str1.lower(), str2.lower())


def is_duplicate_track(
    track_name: str,
    existing_tracks: set[str],
    threshold: float = 90.0,
) -> bool:
    """Check if a track is too similar to any existing tracks.

    Args:
        track_name: Name of the candidate track (format: "Title - Artist").
        existing_tracks: Set of existing track names.
        threshold: Minimum similarity to be considered a duplicate.

    Returns:
        True if the track is a duplicate.
    """
    track_lower = track_name.lower()
    for other in existing_tracks:
        if fuzz.ratio(track_lower, other.lower()) > threshold:
            return True
    return False
