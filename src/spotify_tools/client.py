from pathlib import Path

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from spotify_tools.schemas import SpotifyConfig


class Client(spotipy.Spotify):
    def __init__(self, *args, config: SpotifyConfig, **kwargs):
        auth_manager = SpotifyOAuth(
            client_id=config.CLIENT_ID,
            client_secret=config.CLIENT_SECRET,
            redirect_uri=config.REDIRECT_URI,
            scope="playlist-modify-private playlist-modify-public",
            requests_timeout=30,
            cache_handler=spotipy.CacheFileHandler(
                cache_path=Path(__file__).parent / ".spotipy.cache"
            ),
        )
        super().__init__(*args, auth_manager=auth_manager, **kwargs)
