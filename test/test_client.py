import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

import spotify_tools.client as client_module
from spotify_tools.client import Client, SpotifyConfig


@pytest.fixture(autouse=True)
def clear_env():
    """Clear environment variables used by SpotifyConfig before each test."""
    for var in ["SPOTIFY_TOOLS_CLIENT_ID", "SPOTIFY_TOOLS_CLIENT_SECRET", "SPOTIFY_TOOLS_PLAYLIST_ID", "SPOTIFY_TOOLS_REDIRECT_URI"]:
        os.environ.pop(var, None)
    yield
    # Optionally clear again after test
    for var in ["SPOTIFY_TOOLS_CLIENT_ID", "SPOTIFY_TOOLS_CLIENT_SECRET", "SPOTIFY_TOOLS_PLAYLIST_ID", "SPOTIFY_TOOLS_REDIRECT_URI"]:
        os.environ.pop(var, None)


def test_spotify_config_env_loading():
    os.environ["SPOTIFY_TOOLS_CLIENT_ID"] = "my_client_id"
    os.environ["SPOTIFY_TOOLS_CLIENT_SECRET"] = "my_client_secret"
    os.environ["SPOTIFY_TOOLS_PLAYLIST_ID"] = "my_playlist_id"
    os.environ["SPOTIFY_TOOLS_REDIRECT_URI"] = "https://example.com/callback"

    config = SpotifyConfig()

    assert config.CLIENT_ID == "my_client_id"
    assert config.CLIENT_SECRET == "my_client_secret"
    assert config.PLAYLIST_ID == "my_playlist_id"
    assert config.REDIRECT_URI == "https://example.com/callback"


@patch("spotify_tools.client.SpotifyOAuth")
@patch("spotify_tools.client.spotipy.CacheFileHandler")
@patch("spotify_tools.client.spotipy.Spotify.__init__", return_value=None)
def test_client_init(mock_spotify_init, mock_cache_handler, mock_spotify_oauth):
    # Setup mocks
    mock_cache_handler.return_value = MagicMock()
    mock_auth_manager = MagicMock()
    mock_spotify_oauth.return_value = mock_auth_manager

    config = SpotifyConfig(
        CLIENT_ID="client_id_val",
        CLIENT_SECRET="client_secret_val",
        REDIRECT_URI="https://redirect.uri"
    )

    client = Client(auth_config=config)

    # Assert SpotifyOAuth called with correct args
    mock_spotify_oauth.assert_called_once_with(
        client_id="client_id_val",
        client_secret="client_secret_val",
        redirect_uri="https://redirect.uri",
        scope="playlist-modify-private playlist-modify-public",
        requests_timeout=30,
        cache_handler=mock_cache_handler.return_value,
    )

    # Assert CacheFileHandler called with correct cache_path
    expected_cache_path = Path(client_module.__file__).parent / ".spotipy.cache"
    mock_cache_handler.assert_called_once()
    args, kwargs = mock_cache_handler.call_args
    assert (
        kwargs.get("cache_path") == expected_cache_path
        or (len(args) > 0 and args[0] == expected_cache_path)
    )

    # Assert spotipy.Spotify.__init__ called with auth_manager
    mock_spotify_init.assert_called_once_with(auth_manager=mock_auth_manager)

    # The client instance should be created successfully
    assert isinstance(client, Client)
