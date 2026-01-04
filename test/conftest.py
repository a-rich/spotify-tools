"""Pytest configuration and fixtures."""

import os

import pytest


@pytest.fixture(autouse=True)
def clean_spotify_env():
    """Clear Spotify environment variables for each test."""
    env_vars = [
        "SPOTIFY_TOOLS_CLIENT_ID",
        "SPOTIFY_TOOLS_CLIENT_SECRET",
        "SPOTIFY_TOOLS_PLAYLIST_ID",
        "SPOTIFY_TOOLS_REDIRECT_URI",
    ]

    # Save original values
    original = {var: os.environ.get(var) for var in env_vars}

    # Clear vars
    for var in env_vars:
        os.environ.pop(var, None)

    yield

    # Restore original values
    for var, value in original.items():
        if value is not None:
            os.environ[var] = value
        else:
            os.environ.pop(var, None)

