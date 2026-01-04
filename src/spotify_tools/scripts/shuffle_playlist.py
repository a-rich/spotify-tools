"""Script to create a new playlist from the shuffled tracks of an existing one."""

import random
from datetime import datetime
from typing import Optional

from typer import Option, Typer

from spotify_tools import (
    Client,
    SpotifyConfig,
    get_playlist,
    get_all_playlist_tracks,
    create_playlist,
    get_logger,
)
from spotify_tools.exceptions import (
    InvalidLogLevel,
    NoPlaylistFound,
    NoTracksFound,
)


app = Typer()
logger = get_logger(name="shuffle_playlist")


def resolve_playlist_id(value: Optional[str]) -> str:
    """Resolve playlist ID from CLI arg or environment."""
    if value:
        return value

    config = SpotifyConfig()
    if config.PLAYLIST_ID:
        return config.PLAYLIST_ID

    return ""


def make_new_playlist_name(old_playlist_name: str) -> str:
    """Generate a new playlist name with timestamp."""
    date_string = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"{old_playlist_name} ({date_string})"


@app.command()
def main(
    log_level: Optional[str] = Option(
        None,
        help="Log level.",
    ),
    new_playlist_name: Optional[str] = Option(
        None,
        help=(
            "New playlist name (default is the old playlist's name with a "
            "date string added to it)"
        ),
    ),
    playlist_id: Optional[str] = Option(
        None,
        callback=resolve_playlist_id,
        help=(
            "Spotify playlist ID (or set SPOTIFY_TOOLS_PLAYLIST_ID in the "
            "environment)."
        ),
    ),
    public_playlist: bool = Option(
        False, help="Whether or not the new playlist is public."
    ),
) -> None:
    """Shuffle a playlist and create a new playlist with the shuffled tracks."""
    if log_level is not None:
        try:
            logger.setLevel(log_level)
        except Exception as exc:
            raise InvalidLogLevel(exc) from exc

    if not playlist_id:
        raise NoPlaylistFound(
            "No playlist ID provided. Use --playlist-id or set "
            "SPOTIFY_TOOLS_PLAYLIST_ID in the environment."
        )

    # Initialize client
    client = Client()

    # Get the source playlist
    playlist = get_playlist(client, playlist_id)
    if not playlist:
        raise NoPlaylistFound(f"Could not find playlist with ID: {playlist_id}")

    # Get all tracks from the playlist
    tracks = get_all_playlist_tracks(client, playlist)
    if not tracks:
        raise NoTracksFound(f"No tracks found in playlist '{playlist.name}'")

    logger.info(f"Got {len(tracks)} tracks from '{playlist.name}'")

    # Shuffle the tracks
    random.shuffle(tracks)

    # Generate new playlist name if not provided
    if new_playlist_name is None:
        new_playlist_name = make_new_playlist_name(playlist.name)

    # Create the new playlist
    new_playlist = create_playlist(
        client=client,
        name=new_playlist_name,
        tracks=tracks,
        public=public_playlist,
        description=f"Shuffled version of {playlist.name}",
    )

    if new_playlist and new_playlist.external_urls:
        logger.info(
            f"Created shuffled playlist '{new_playlist_name}': "
            f"{new_playlist.external_urls.spotify}"
        )


if __name__ == "__main__":
    app()
