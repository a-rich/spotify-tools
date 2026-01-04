"""spotify-tools: A clean, general-purpose library for interacting with Spotify.

This library provides simplified interfaces for common Spotify operations:
- Searching for tracks with fuzzy matching
- Getting tracks from playlists
- Creating and updating playlists
- Managing playlist contents with LIFO queue behavior

Basic usage:
    from spotify_tools import Client, search_track_fuzzy, create_playlist

    # Create a client (credentials from environment or config)
    client = Client()

    # Search for a track with fuzzy matching
    result = search_track_fuzzy(client, "Song Title", "Artist Name")

    # Get tracks from a playlist
    tracks = get_playlist_tracks(client, "playlist_id")

    # Create a new playlist
    playlist = create_playlist(client, "My Playlist", tracks)
"""

# Client
from spotify_tools.client import (
    Client,
    DEFAULT_SCOPES,
    get_client,
    validate_credentials,
)

# Configuration and schemas
from spotify_tools.schemas import (
    SpotifyConfig,
    # Response types
    PlaylistResponse,
    Track,
    Tracks,
    Item,
    Album,
    Artist,
    User,
    # Search results
    TrackSearchResults,
)

# Search functionality
from spotify_tools.search import (
    SearchType,
    SearchResult,
    search_tracks,
    search_track,
    search_track_fuzzy,
    search_track_with_pagination,
    filter_tracks_by_similarity,
    batch_search_tracks,
    calculate_similarity,
    is_duplicate_track,
)

# Playlist operations
from spotify_tools.playlists import (
    PlaylistTrack,
    UpdateResult,
    get_playlist,
    get_playlist_tracks,
    get_all_playlist_tracks,
    get_current_user,
    create_playlist,
    add_tracks_to_playlist,
    remove_tracks_from_playlist,
    update_playlist,
    get_or_create_playlist,
    resolve_track_from_url,
)

# Exceptions
from spotify_tools.exceptions import (
    InvalidLogLevel,
    NoPlaylistFound,
    NoTracksFound,
)

# Logging
from spotify_tools.logging import get_logger


__version__ = "0.0.1"

__all__ = [
    # Version
    "__version__",
    # Client
    "Client",
    "DEFAULT_SCOPES",
    "get_client",
    "validate_credentials",
    # Config
    "SpotifyConfig",
    # Schemas
    "PlaylistResponse",
    "Track",
    "Tracks",
    "Item",
    "Album",
    "Artist",
    "User",
    "TrackSearchResults",
    # Search
    "SearchType",
    "SearchResult",
    "search_tracks",
    "search_track",
    "search_track_fuzzy",
    "search_track_with_pagination",
    "filter_tracks_by_similarity",
    "batch_search_tracks",
    "calculate_similarity",
    "is_duplicate_track",
    # Playlists
    "PlaylistTrack",
    "UpdateResult",
    "get_playlist",
    "get_playlist_tracks",
    "get_all_playlist_tracks",
    "get_current_user",
    "create_playlist",
    "add_tracks_to_playlist",
    "remove_tracks_from_playlist",
    "update_playlist",
    "get_or_create_playlist",
    "resolve_track_from_url",
    # Exceptions
    "InvalidLogLevel",
    "NoPlaylistFound",
    "NoTracksFound",
    # Logging
    "get_logger",
]

