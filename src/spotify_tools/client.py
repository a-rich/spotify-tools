from pathlib import Path

import spotipy
from pydantic_settings import BaseSettings, SettingsConfigDict
from spotipy.oauth2 import SpotifyOAuth


class SpotifyConfig(BaseSettings):
    CLIENT_ID: str = ""
    CLIENT_SECRET: str = ""
    PLAYLIST_ID: str = ""
    REDIRECT_URI: str = ""

    model_config = SettingsConfigDict(env_prefix="SPOTIFY_TOOLS_")


class Client(spotipy.Spotify):
    def __init__(self, *args, auth_config: SpotifyConfig, **kwargs):
        auth_manager = SpotifyOAuth(
            client_id=auth_config.CLIENT_ID,
            client_secret=auth_config.CLIENT_SECRET,
            redirect_uri=auth_config.REDIRECT_URI,
            scope="playlist-modify-private playlist-modify-public",
            requests_timeout=30,
            cache_handler=spotipy.CacheFileHandler(
                cache_path=Path(__file__).parent / ".spotipy.cache"
            ),
        )
        super().__init__(*args, auth_manager=auth_manager, **kwargs)
