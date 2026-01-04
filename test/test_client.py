"""Tests for the Spotify client module."""

import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

import spotify_tools.client as client_module
from spotify_tools.client import Client, DEFAULT_SCOPES
from spotify_tools.schemas import SpotifyConfig


@pytest.fixture(autouse=True)
def clear_env():
    """Clear environment variables used by SpotifyConfig before each test."""
    env_vars = [
        "SPOTIFY_TOOLS_CLIENT_ID",
        "SPOTIFY_TOOLS_CLIENT_SECRET",
        "SPOTIFY_TOOLS_PLAYLIST_ID",
        "SPOTIFY_TOOLS_REDIRECT_URI",
    ]
    for var in env_vars:
        os.environ.pop(var, None)
    yield
    for var in env_vars:
        os.environ.pop(var, None)


def test_spotify_config_env_loading():
    """Test that SpotifyConfig loads values from environment variables."""
    os.environ["SPOTIFY_TOOLS_CLIENT_ID"] = "my_client_id"
    os.environ["SPOTIFY_TOOLS_CLIENT_SECRET"] = "my_client_secret"
    os.environ["SPOTIFY_TOOLS_PLAYLIST_ID"] = "my_playlist_id"
    os.environ["SPOTIFY_TOOLS_REDIRECT_URI"] = "https://example.com/callback"

    config = SpotifyConfig()

    assert config.CLIENT_ID == "my_client_id"
    assert config.CLIENT_SECRET == "my_client_secret"
    assert config.PLAYLIST_ID == "my_playlist_id"
    assert config.REDIRECT_URI == "https://example.com/callback"


def test_spotify_config_default_values():
    """Test that SpotifyConfig has empty defaults."""
    config = SpotifyConfig()

    assert config.CLIENT_ID == ""
    assert config.CLIENT_SECRET == ""
    assert config.PLAYLIST_ID == ""
    assert config.REDIRECT_URI == ""


def test_spotify_config_explicit_values():
    """Test that SpotifyConfig accepts explicit values."""
    config = SpotifyConfig(
        CLIENT_ID="explicit_id",
        CLIENT_SECRET="explicit_secret",
        PLAYLIST_ID="explicit_playlist",
        REDIRECT_URI="https://explicit.url",
    )

    assert config.CLIENT_ID == "explicit_id"
    assert config.CLIENT_SECRET == "explicit_secret"
    assert config.PLAYLIST_ID == "explicit_playlist"
    assert config.REDIRECT_URI == "https://explicit.url"


@patch("spotify_tools.client.SpotifyOAuth")
@patch("spotify_tools.client.spotipy.CacheFileHandler")
@patch("spotify_tools.client.spotipy.Spotify.__init__", return_value=None)
def test_client_init_with_config(
    mock_spotify_init, mock_cache_handler, mock_spotify_oauth
):
    """Test Client initialization with explicit config."""
    mock_cache_handler.return_value = MagicMock()
    mock_auth_manager = MagicMock()
    mock_spotify_oauth.return_value = mock_auth_manager

    config = SpotifyConfig(
        CLIENT_ID="client_id_val",
        CLIENT_SECRET="client_secret_val",
        REDIRECT_URI="https://redirect.uri",
    )

    client = Client(config=config)

    # Assert SpotifyOAuth called with correct args
    mock_spotify_oauth.assert_called_once_with(
        client_id="client_id_val",
        client_secret="client_secret_val",
        redirect_uri="https://redirect.uri",
        scope=" ".join(DEFAULT_SCOPES),
        requests_timeout=30,
        cache_handler=mock_cache_handler.return_value,
    )

    # Assert CacheFileHandler called with correct cache_path
    expected_cache_path = (
        Path(client_module.__file__).parent / ".spotipy.cache"
    )
    mock_cache_handler.assert_called_once()
    _, kwargs = mock_cache_handler.call_args
    assert kwargs.get("cache_path") == expected_cache_path

    # Assert spotipy.Spotify.__init__ called with auth_manager
    mock_spotify_init.assert_called_once_with(auth_manager=mock_auth_manager)

    # Client should be created successfully
    assert isinstance(client, Client)
    assert client.config == config


@patch("spotify_tools.client.SpotifyOAuth")
@patch("spotify_tools.client.spotipy.CacheFileHandler")
@patch("spotify_tools.client.spotipy.Spotify.__init__", return_value=None)
def test_client_init_with_custom_scopes(
    mock_spotify_init, mock_cache_handler, mock_spotify_oauth
):
    """Test Client initialization with custom scopes."""
    mock_cache_handler.return_value = MagicMock()
    mock_auth_manager = MagicMock()
    mock_spotify_oauth.return_value = mock_auth_manager

    custom_scopes = ["playlist-read-private", "user-library-read"]

    config = SpotifyConfig(
        CLIENT_ID="test_id",
        CLIENT_SECRET="test_secret",
        REDIRECT_URI="https://test.uri",
    )

    Client(config=config, scopes=custom_scopes)

    # Verify custom scopes were used
    call_kwargs = mock_spotify_oauth.call_args[1]
    assert call_kwargs["scope"] == " ".join(custom_scopes)


@patch("spotify_tools.client.SpotifyOAuth")
@patch("spotify_tools.client.spotipy.CacheFileHandler")
@patch("spotify_tools.client.spotipy.Spotify.__init__", return_value=None)
def test_client_init_with_custom_cache_path(
    mock_spotify_init, mock_cache_handler, mock_spotify_oauth
):
    """Test Client initialization with custom cache path."""
    mock_cache_handler.return_value = MagicMock()
    mock_spotify_oauth.return_value = MagicMock()

    custom_cache = Path("/tmp/custom_cache.json")

    config = SpotifyConfig(
        CLIENT_ID="test_id",
        CLIENT_SECRET="test_secret",
        REDIRECT_URI="https://test.uri",
    )

    Client(config=config, cache_path=custom_cache)

    # Verify custom cache path was used
    _, kwargs = mock_cache_handler.call_args
    assert kwargs.get("cache_path") == custom_cache


@patch("spotify_tools.client.SpotifyOAuth")
@patch("spotify_tools.client.spotipy.CacheFileHandler")
@patch("spotify_tools.client.spotipy.Spotify.__init__", return_value=None)
def test_client_init_without_config_uses_env(
    mock_spotify_init, mock_cache_handler, mock_spotify_oauth
):
    """Test Client initialization without config loads from environment."""
    os.environ["SPOTIFY_TOOLS_CLIENT_ID"] = "env_client_id"
    os.environ["SPOTIFY_TOOLS_CLIENT_SECRET"] = "env_client_secret"
    os.environ["SPOTIFY_TOOLS_REDIRECT_URI"] = "https://env.redirect"

    mock_cache_handler.return_value = MagicMock()
    mock_spotify_oauth.return_value = MagicMock()

    client = Client()

    # Verify environment values were used
    call_kwargs = mock_spotify_oauth.call_args[1]
    assert call_kwargs["client_id"] == "env_client_id"
    assert call_kwargs["client_secret"] == "env_client_secret"
    assert call_kwargs["redirect_uri"] == "https://env.redirect"

    # Config should be accessible
    assert client.config.CLIENT_ID == "env_client_id"


def test_default_scopes_content():
    """Test that DEFAULT_SCOPES contains expected scopes."""
    assert "playlist-modify-private" in DEFAULT_SCOPES
    assert "playlist-modify-public" in DEFAULT_SCOPES
    assert "playlist-read-private" in DEFAULT_SCOPES
    assert "user-read-private" in DEFAULT_SCOPES
