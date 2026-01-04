"""This script is used to create a new playlist from the shuffled tracks of an
existing playlist.
"""

import random
from datetime import datetime
from typing import Optional

from typer import Option, Typer

from spotify_tools.client import Client
from spotify_tools.exceptions import (
    InvalidLogLevel,
    NoPlaylistFound,
    NoTracksFound,
)
from spotify_tools.logging import get_logger
from spotify_tools.schemas import (
    Item,
    PlaylistResponse,
    SpotifyConfig,
    Tracks,
    TrackSearchResults,
    User,
)


app = Typer()
logger = get_logger(name="shuffle_playlist")


def resolve_playlist_id(value: Optional[str]) -> str:
    # Use the playlist ID provided via the CLI
    if value:
        return value

    # Otherwise load the playlist ID from the environment
    config = SpotifyConfig()
    if config.PLAYLIST_ID:
        return config.PLAYLIST_ID


def get_all_playlist_tracks(
    client: Client, playlist: PlaylistResponse
) -> list[Item]:
    all_items: list[Item] = playlist.tracks.items or []

    while playlist.tracks.next:
        tracks: Tracks = Tracks.model_validate(
            client.next(playlist.tracks.model_dump())
        )
        all_items.extend(tracks.items)
        playlist.tracks = tracks

    logger.info(f"Got {len(all_items)} tracks from '{playlist.name}'")

    return all_items


def make_new_playlist_name(old_playlist_name: str) -> str:
    date_string = datetime.now().strftime("%Y-%m-%d %H:%M")

    return f"{old_playlist_name} ({date_string})"


def shuffle_and_create_new_playlist(
    client: Client,
    tracks: list[Item],
    old_playlist_name: str,
    new_playlist_name: str,
    public_playlist: bool,
) -> PlaylistResponse:
    random.shuffle(tracks)
    track_uris = [
        item.track.uri for item in tracks if item.track and item.track.uri
    ]
    user = User.model_validate(client.me())
    new_playlist = PlaylistResponse.model_validate(
        client.user_playlist_create(
            user=user.id,
            name=new_playlist_name,
            public=public_playlist,
            description=f"Shuffled version of {old_playlist_name}",
        )
    )

    for i in range(0, len(track_uris), 100):
        client.playlist_add_items(new_playlist.id, track_uris[i : i + 100])

    logger.info(
        f"Shuffled '{new_playlist_name}': {new_playlist.external_urls.spotify}"
    )

    return new_playlist


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
            "Spotify playlist ID (or set SPOTIFY_TOOLS_PLAYLIST_ID in the environment)."
        ),
    ),
    public_playlist: bool = Option(
        False, help="Whether or not the new playlist is public."
    ),
) -> None:
    if log_level is not None:
        try:
            logger.setLevel(log_level)
        except Exception as exc:
            raise InvalidLogLevel(exc)

    config = SpotifyConfig(PLAYLIST_ID=playlist_id)
    client = Client(config=config)
    
    # results = client.search(
    #     q="track:The Dreamers artist:Hobzee, Wagz",
    #     limit=5,
    #     type="track",
    # )
    # tracks = TrackSearchResults.model_validate(results["tracks"])

    # breakpoint()

    try:
        playlist_resp = client.playlist(playlist_id)
    except Exception as exc:
        raise NoPlaylistFound(exc)

    playlist = PlaylistResponse.model_validate(playlist_resp)
    tracks = get_all_playlist_tracks(client, playlist)

    if not tracks:
        raise NoTracksFound(f"No tracks found for '{playlist.name}'")

    if new_playlist_name is None:
        new_playlist_name = make_new_playlist_name(playlist.name)

    shuffle_and_create_new_playlist(
        client=client,
        tracks=tracks,
        old_playlist_name=playlist.name,
        new_playlist_name=new_playlist_name,
        public_playlist=public_playlist,
    )


if __name__ == "__main__":
    app()
