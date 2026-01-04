"""Playlist operations for Spotify."""

from dataclasses import dataclass
from typing import Optional

from spotify_tools.logging import get_logger
from spotify_tools.schemas import (
    Item,
    PlaylistResponse,
    Track,
    Tracks,
    User,
)
from spotify_tools.search import is_duplicate_track


logger = get_logger(__name__)


@dataclass
class PlaylistTrack:
    """Representation of a track in a playlist context."""

    id: str
    uri: str
    name: str
    artists: str

    @classmethod
    def from_item(cls, item: Item) -> Optional["PlaylistTrack"]:
        """Create a PlaylistTrack from a playlist Item."""
        if not item.track or not item.track.id:
            return None

        artists = ""
        if item.track.artists:
            artists = ", ".join(
                a.name for a in item.track.artists if a.name
            )

        return cls(
            id=item.track.id,
            uri=item.track.uri or f"spotify:track:{item.track.id}",
            name=item.track.name or "",
            artists=artists,
        )

    @classmethod
    def from_track(cls, track: Track) -> Optional["PlaylistTrack"]:
        """Create a PlaylistTrack from a Track object."""
        if not track or not track.id:
            return None

        artists = ""
        if track.artists:
            artists = ", ".join(a.name for a in track.artists if a.name)

        return cls(
            id=track.id,
            uri=track.uri or f"spotify:track:{track.id}",
            name=track.name or "",
            artists=artists,
        )

    @property
    def display_name(self) -> str:
        """Get display name in 'Title - Artist' format."""
        if self.artists:
            return f"{self.name} - {self.artists}"
        return self.name


def get_playlist(client, playlist_id: str) -> Optional[PlaylistResponse]:
    """Get a playlist by ID.

    Args:
        client: Spotify client.
        playlist_id: Spotify playlist ID.

    Returns:
        PlaylistResponse object or None if not found.
    """
    try:
        response = client.playlist(playlist_id)
        return PlaylistResponse.model_validate(response)
    except Exception as exc:
        logger.warning(f"Failed to get playlist {playlist_id}: {exc}")
        return None


def get_playlist_tracks(client, playlist_id: str) -> list[PlaylistTrack]:
    """Get all tracks from a playlist.

    Handles pagination to retrieve all tracks regardless of playlist size.

    Args:
        client: Spotify client.
        playlist_id: Spotify playlist ID.

    Returns:
        List of PlaylistTrack objects.
    """
    playlist = get_playlist(client, playlist_id)
    if not playlist or not playlist.tracks:
        return []

    return get_all_playlist_tracks(client, playlist)


def get_all_playlist_tracks(
    client, playlist: PlaylistResponse
) -> list[PlaylistTrack]:
    """Get all tracks from a PlaylistResponse, handling pagination.

    Args:
        client: Spotify client.
        playlist: PlaylistResponse object.

    Returns:
        List of PlaylistTrack objects.
    """
    if not playlist.tracks:
        return []

    all_items: list[Item] = playlist.tracks.items or []
    tracks_data = playlist.tracks

    # Paginate through all tracks
    while tracks_data.next:
        try:
            next_response = client.next(tracks_data.model_dump())
            if not next_response:
                break
            tracks_data = Tracks.model_validate(next_response)
            all_items.extend(tracks_data.items or [])
        except Exception as exc:
            logger.warning(f"Failed to get next page of tracks: {exc}")
            break

    # Convert to PlaylistTrack objects
    playlist_tracks = []
    for item in all_items:
        pt = PlaylistTrack.from_item(item)
        if pt:
            playlist_tracks.append(pt)

    logger.info(f"Got {len(playlist_tracks)} tracks from '{playlist.name}'")
    return playlist_tracks


def get_current_user(client) -> Optional[User]:
    """Get the current authenticated user.

    Args:
        client: Spotify client.

    Returns:
        User object or None.
    """
    try:
        response = client.me()
        return User.model_validate(response)
    except Exception as exc:
        logger.warning(f"Failed to get current user: {exc}")
        return None


def create_playlist(
    client,
    name: str,
    tracks: list[PlaylistTrack],
    public: bool = False,
    description: str = "",
    user_id: Optional[str] = None,
) -> Optional[PlaylistResponse]:
    """Create a new playlist with the given tracks.

    Args:
        client: Spotify client.
        name: Name for the new playlist.
        tracks: List of tracks to add.
        public: Whether the playlist should be public.
        description: Optional playlist description.
        user_id: User ID to create playlist for. If None, uses current user.

    Returns:
        PlaylistResponse for the new playlist, or None on failure.
    """
    if user_id is None:
        user = get_current_user(client)
        if not user or not user.id:
            logger.error("Could not determine user ID for playlist creation")
            return None
        user_id = user.id

    try:
        playlist_response = client.user_playlist_create(
            user=user_id,
            name=name,
            public=public,
            description=description,
        )
        playlist = PlaylistResponse.model_validate(playlist_response)
    except Exception as exc:
        logger.error(f"Failed to create playlist '{name}': {exc}")
        return None

    if not playlist.id:
        logger.error(f"Created playlist '{name}' but got no ID")
        return None

    # Add tracks in batches of 100 (Spotify API limit)
    if tracks:
        track_uris = [t.uri for t in tracks]
        add_tracks_to_playlist(client, playlist.id, track_uris)

    logger.info(
        f"Created playlist '{name}' with {len(tracks)} tracks: "
        f"{playlist.external_urls.spotify if playlist.external_urls else ''}"
    )

    return playlist


def add_tracks_to_playlist(
    client,
    playlist_id: str,
    track_uris: list[str],
    position: Optional[int] = None,
) -> bool:
    """Add tracks to a playlist.

    Args:
        client: Spotify client.
        playlist_id: Playlist ID to add tracks to.
        track_uris: List of track URIs to add.
        position: Position to insert tracks. None appends to end.

    Returns:
        True if successful.
    """
    if not track_uris:
        return True

    try:
        # Add in batches of 100
        for i in range(0, len(track_uris), 100):
            batch = track_uris[i:i + 100]
            if position is not None:
                client.playlist_add_items(
                    playlist_id, batch, position=position + i
                )
            else:
                client.playlist_add_items(playlist_id, batch)
        return True
    except Exception as exc:
        logger.error(f"Failed to add tracks to playlist: {exc}")
        return False


def remove_tracks_from_playlist(
    client,
    playlist_id: str,
    tracks_to_remove: list[dict],
) -> bool:
    """Remove specific tracks from a playlist.

    Args:
        client: Spotify client.
        playlist_id: Playlist ID.
        tracks_to_remove: List of dicts with 'uri' and 'positions' keys.

    Returns:
        True if successful.
    """
    if not tracks_to_remove:
        return True

    try:
        client.playlist_remove_specific_occurrences_of_items(
            playlist_id, tracks_to_remove
        )
        return True
    except Exception as exc:
        logger.error(f"Failed to remove tracks from playlist: {exc}")
        return False


@dataclass
class UpdateResult:
    """Result of a playlist update operation."""

    tracks_added: list[PlaylistTrack]
    tracks_removed: list[PlaylistTrack]
    skipped_duplicates: list[PlaylistTrack]
    skipped_existing: list[PlaylistTrack]


def update_playlist(
    client,
    playlist_id: str,
    new_tracks: list[PlaylistTrack],
    max_size: Optional[int] = None,
    check_duplicates: bool = True,
    duplicate_threshold: float = 90.0,
    verbosity: int = 0,
) -> UpdateResult:
    """Update an existing playlist with new tracks (LIFO queue behavior).

    New tracks are added to the playlist. If adding them would exceed max_size,
    the oldest tracks (from the beginning) are removed to make room.

    Args:
        client: Spotify client.
        playlist_id: Playlist ID to update.
        new_tracks: List of new tracks to add.
        max_size: Maximum playlist size. If None, no limit.
        check_duplicates: Check for duplicate/similar tracks.
        duplicate_threshold: Similarity threshold for duplicate detection.
        verbosity: Logging verbosity level.

    Returns:
        UpdateResult with details of the operation.
    """
    result = UpdateResult(
        tracks_added=[],
        tracks_removed=[],
        skipped_duplicates=[],
        skipped_existing=[],
    )

    # Get current playlist tracks
    current_tracks = get_playlist_tracks(client, playlist_id)
    current_ids = {t.id for t in current_tracks}
    current_names = {t.display_name for t in current_tracks}

    # Filter new tracks
    tracks_to_add: list[PlaylistTrack] = []
    for track in new_tracks:
        # Check if already in playlist by ID
        if track.id in current_ids:
            result.skipped_existing.append(track)
            if verbosity > 0:
                logger.warning(
                    f'Track "{track.display_name}" already in playlist'
                )
            continue

        # Check for similar tracks by name
        if check_duplicates and is_duplicate_track(
            track.display_name, current_names, duplicate_threshold
        ):
            result.skipped_duplicates.append(track)
            if verbosity > 0:
                logger.warning(
                    f'Track "{track.display_name}" too similar to existing'
                )
            continue

        tracks_to_add.append(track)
        current_names.add(track.display_name)

    if not tracks_to_add:
        logger.info("No new tracks to add")
        return result

    # Calculate tracks to remove if we'd exceed max_size
    tracks_to_remove: list[PlaylistTrack] = []
    if max_size is not None:
        new_total = len(current_tracks) + len(tracks_to_add)
        if new_total > max_size:
            excess = new_total - max_size
            # Remove from the beginning (oldest tracks)
            tracks_to_remove = current_tracks[:excess]

    # Perform removal first
    if tracks_to_remove:
        remove_payload = [
            {"uri": t.uri, "positions": [i]}
            for i, t in enumerate(tracks_to_remove)
        ]
        if remove_tracks_from_playlist(client, playlist_id, remove_payload):
            result.tracks_removed = tracks_to_remove
            if verbosity > 0:
                logger.info(f"Removed {len(tracks_to_remove)} old tracks")
                for t in tracks_to_remove:
                    logger.info(f"\t{t.display_name}")

    # Add new tracks
    track_uris = [t.uri for t in tracks_to_add]
    if add_tracks_to_playlist(client, playlist_id, track_uris):
        result.tracks_added = tracks_to_add
        logger.info(f"Added {len(tracks_to_add)} new tracks")
        if verbosity > 0:
            for t in tracks_to_add:
                logger.info(f"\t{t.display_name}")

    return result


def get_or_create_playlist(
    client,
    name: str,
    public: bool = False,
    description: str = "",
    user_id: Optional[str] = None,
) -> Optional[PlaylistResponse]:
    """Get an existing playlist by name or create a new one.

    Searches the current user's playlists for one matching the given name.
    If not found, creates a new playlist.

    Args:
        client: Spotify client.
        name: Playlist name.
        public: Whether new playlist should be public.
        description: Description for new playlist.
        user_id: User ID. If None, uses current user.

    Returns:
        PlaylistResponse or None.
    """
    if user_id is None:
        user = get_current_user(client)
        if not user or not user.id:
            return None
        user_id = user.id

    # Search user's playlists
    try:
        playlists = client.user_playlists(user_id, limit=50)
        while playlists:
            for playlist in playlists.get("items", []):
                if playlist.get("name") == name:
                    return PlaylistResponse.model_validate(
                        client.playlist(playlist["id"])
                    )
            if playlists.get("next"):
                playlists = client.next(playlists)
            else:
                break
    except Exception as exc:
        logger.warning(f"Error searching playlists: {exc}")

    # Not found, create new
    return create_playlist(
        client,
        name=name,
        tracks=[],
        public=public,
        description=description,
        user_id=user_id,
    )


def resolve_track_from_url(client, url: str) -> Optional[PlaylistTrack]:
    """Resolve a Spotify track URL to a PlaylistTrack.

    Args:
        client: Spotify client.
        url: Spotify track URL (e.g. https://open.spotify.com/track/...).

    Returns:
        PlaylistTrack or None.
    """
    try:
        response = client.track(url)
        if response:
            # Create a mock Track to use from_track
            from spotify_tools.schemas import Track as TrackSchema
            track = TrackSchema.model_validate(response)
            return PlaylistTrack.from_track(track)
    except Exception as exc:
        logger.warning(f"Failed to resolve track URL '{url}': {exc}")

    return None

