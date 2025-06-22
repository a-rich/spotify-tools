"""This script is used to create a new playlist from the shuffled tracks of an
existing playlist.
"""

import asyncio
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
    to_dict,
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


def make_new_playlist_name(old_playlist_name: str) -> str:
    date_string = datetime.now().strftime("%Y-%m-%d %H:%M")

    return f"{old_playlist_name} ({date_string})"


async def shuffle_and_create_new_playlist(
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
    # TODO: figure out how to get auth working with spotipy2
    res = await client._get("me")
    print(res)
    user = User.model_validate(await client.me())
    new_playlist = PlaylistResponse.model_validate(
        await client.user_playlist_create(
            user=user.id,
            name=new_playlist_name,
            public=public_playlist,
            description=f"Shuffled version of {old_playlist_name}",
        )
    )

    for i in range(0, len(track_uris), 100):
        await client.playlist_add_items(
            new_playlist.id, track_uris[i : i + 100]
        )

    logger.info(
        f"Shuffled '{new_playlist_name}': {new_playlist.external_urls.spotify}"
    )

    return new_playlist


async def run(
    log_level: str,
    new_playlist_name: str,
    playlist_id: str,
    public_playlist: bool,
) -> None:
    if log_level is not None:
        try:
            logger.setLevel(log_level)
        except Exception as exc:
            raise InvalidLogLevel(exc)

    if not playlist_id:
        config = SpotifyConfig()
    else:
        config = SpotifyConfig(PLAYLIST_ID=playlist_id)

    client = Client(config=config)

    try:
        playlist_resp = await client.get_playlist(playlist_id)
    except Exception as exc:
        raise NoPlaylistFound(exc)

    playlist = PlaylistResponse.model_validate(to_dict(playlist_resp))
    tracks = [
        Item.model_validate(to_dict(track))
        async for track in client.iter_playlist_tracks(playlist_id)
    ]

    if not tracks:
        raise NoTracksFound(f"No tracks found for '{playlist.name}'")

    if new_playlist_name is None:
        new_playlist_name = make_new_playlist_name(playlist.name)

    await shuffle_and_create_new_playlist(
        client=client,
        tracks=tracks,
        old_playlist_name=playlist.name,
        new_playlist_name=new_playlist_name,
        public_playlist=public_playlist,
    )


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
    asyncio.run(
        run(
            log_level=log_level,
            new_playlist_name=new_playlist_name,
            playlist_id=playlist_id,
            public_playlist=public_playlist,
        )
    )


if __name__ == "__main__":
    app()
