"""Spotify client wrapper with authentication handling."""

from pathlib import Path
from typing import Optional

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from spotify_tools.schemas import SpotifyConfig


# Default scopes for spotify-tools
DEFAULT_SCOPES = [
    "playlist-modify-private",
    "playlist-modify-public",
    "playlist-read-private",
    "playlist-read-collaborative",
    "user-read-private",
    "user-read-email",
]


class Client(spotipy.Spotify):
    """Spotify API client with simplified authentication.

    Extends spotipy.Spotify with convenient configuration handling.
    Credentials can be provided via SpotifyConfig or environment variables:
        - SPOTIFY_TOOLS_CLIENT_ID
        - SPOTIFY_TOOLS_CLIENT_SECRET
        - SPOTIFY_TOOLS_REDIRECT_URI
    """

    def __init__(
        self,
        *args,
        config: Optional[SpotifyConfig] = None,
        scopes: Optional[list[str]] = None,
        cache_path: Optional[Path] = None,
        requests_timeout: int = 30,
        **kwargs,
    ):
        """Initialize the Spotify client.

        Args:
            config: SpotifyConfig with credentials. If None, loads from env.
            scopes: List of OAuth scopes. If None, uses DEFAULT_SCOPES.
            cache_path: Path for token cache. If None, uses default location.
            requests_timeout: Request timeout in seconds.
            *args: Additional positional args for spotipy.Spotify.
            **kwargs: Additional keyword args for spotipy.Spotify.
        """
        if config is None:
            config = SpotifyConfig()

        if scopes is None:
            scopes = DEFAULT_SCOPES

        if cache_path is None:
            cache_path = Path(__file__).parent / ".spotipy.cache"

        auth_manager = SpotifyOAuth(
            client_id=config.CLIENT_ID,
            client_secret=config.CLIENT_SECRET,
            redirect_uri=config.REDIRECT_URI,
            scope=" ".join(scopes),
            requests_timeout=requests_timeout,
            cache_handler=spotipy.CacheFileHandler(cache_path=cache_path),
        )

        super().__init__(*args, auth_manager=auth_manager, **kwargs)

        self._config = config

    @property
    def config(self) -> SpotifyConfig:
        """Get the client's configuration."""
        return self._config


def get_client(
    config: Optional[SpotifyConfig] = None,
    scopes: Optional[list[str]] = None,
) -> Client:
    """Create a Spotify client.

    Convenience function for creating a Client instance.

    Args:
        config: SpotifyConfig with credentials. If None, loads from env.
        scopes: List of OAuth scopes. If None, uses default scopes.

    Returns:
        Configured Client instance.
    """
    return Client(config=config, scopes=scopes)


def validate_credentials(client: Client) -> bool:
    """Validate that the client has valid credentials.

    Args:
        client: Spotify client to validate.

    Returns:
        True if credentials are valid.

    Raises:
        RuntimeError: If credentials are invalid.
    """
    try:
        client.current_user()
        return True
    except Exception as exc:
        raise RuntimeError("Spotify credentials are invalid!") from exc
