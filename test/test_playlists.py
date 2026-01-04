"""Tests for the playlists module."""

from unittest.mock import MagicMock

import pytest

from spotify_tools.schemas import (
    Track,
    Artist,
    Item,
    Tracks,
    PlaylistResponse,
    User,
    ExternalUrls,
)
from spotify_tools.playlists import (
    PlaylistTrack,
    get_playlist,
    get_playlist_tracks,
    create_playlist,
    add_tracks_to_playlist,
    update_playlist,
    get_or_create_playlist,
    resolve_track_from_url,
)


@pytest.fixture
def mock_client():
    """Create a mock Spotify client."""
    return MagicMock()


@pytest.fixture
def sample_track():
    """Create a sample Track object."""
    return Track(
        id="track123",
        name="Test Song",
        uri="spotify:track:track123",
        artists=[Artist(name="Test Artist")],
    )


@pytest.fixture
def sample_item(sample_track):
    """Create a sample playlist Item."""
    return Item(track=sample_track)


@pytest.fixture
def sample_playlist_response(sample_item):
    """Create a sample PlaylistResponse."""
    return PlaylistResponse(
        id="playlist123",
        name="Test Playlist",
        external_urls=ExternalUrls(spotify="https://open.spotify.com/playlist/123"),
        tracks=Tracks(
            items=[sample_item],
            next=None,
            total=1,
        ),
    )


@pytest.fixture
def sample_user():
    """Create a sample User."""
    return User(id="user123", display_name="Test User")


class TestPlaylistTrack:
    """Tests for PlaylistTrack dataclass."""

    def test_from_item(self, sample_item):
        """Test creating PlaylistTrack from Item."""
        pt = PlaylistTrack.from_item(sample_item)

        assert pt is not None
        assert pt.id == "track123"
        assert pt.name == "Test Song"
        assert pt.artists == "Test Artist"
        assert pt.uri == "spotify:track:track123"

    def test_from_item_none_track(self):
        """Test from_item returns None for Item without track."""
        item = Item(track=None)
        pt = PlaylistTrack.from_item(item)
        assert pt is None

    def test_from_track(self, sample_track):
        """Test creating PlaylistTrack from Track."""
        pt = PlaylistTrack.from_track(sample_track)

        assert pt is not None
        assert pt.id == "track123"
        assert pt.name == "Test Song"

    def test_display_name(self):
        """Test display_name property."""
        pt = PlaylistTrack(
            id="1", uri="uri", name="Song", artists="Artist1, Artist2"
        )
        assert pt.display_name == "Song - Artist1, Artist2"

    def test_display_name_no_artists(self):
        """Test display_name with no artists."""
        pt = PlaylistTrack(id="1", uri="uri", name="Song", artists="")
        assert pt.display_name == "Song"


class TestGetPlaylist:
    """Tests for get_playlist function."""

    def test_get_playlist_success(self, mock_client, sample_playlist_response):
        """Test successful playlist retrieval."""
        mock_client.playlist.return_value = sample_playlist_response.model_dump()

        result = get_playlist(mock_client, "playlist123")

        assert result is not None
        assert result.id == "playlist123"
        assert result.name == "Test Playlist"

    def test_get_playlist_not_found(self, mock_client):
        """Test playlist not found returns None."""
        mock_client.playlist.side_effect = Exception("Not found")

        result = get_playlist(mock_client, "invalid")

        assert result is None


class TestGetPlaylistTracks:
    """Tests for playlist track retrieval."""

    def test_get_playlist_tracks(self, mock_client, sample_playlist_response):
        """Test getting tracks from a playlist."""
        mock_client.playlist.return_value = sample_playlist_response.model_dump()

        tracks = get_playlist_tracks(mock_client, "playlist123")

        assert len(tracks) == 1
        assert tracks[0].name == "Test Song"

    def test_get_playlist_tracks_with_pagination(self, mock_client):
        """Test pagination when getting playlist tracks."""
        # First page
        first_track = Item(track=Track(
            id="track1", name="Song 1", uri="uri1", artists=[]
        ))
        first_page = PlaylistResponse(
            id="playlist123",
            name="Test",
            tracks=Tracks(
                items=[first_track],
                next="http://next-page",
                total=2,
            ),
        )

        # Second page
        second_track_data = {
            "items": [{"track": {
                "id": "track2", "name": "Song 2", "uri": "uri2", "artists": []
            }}],
            "next": None,
        }

        mock_client.playlist.return_value = first_page.model_dump()
        mock_client.next.return_value = second_track_data

        tracks = get_playlist_tracks(mock_client, "playlist123")

        assert len(tracks) == 2
        assert tracks[0].id == "track1"
        assert tracks[1].id == "track2"


class TestCreatePlaylist:
    """Tests for playlist creation."""

    def test_create_playlist_success(
        self, mock_client, sample_user, sample_playlist_response
    ):
        """Test successful playlist creation."""
        mock_client.me.return_value = sample_user.model_dump()
        mock_client.user_playlist_create.return_value = (
            sample_playlist_response.model_dump()
        )

        tracks = [
            PlaylistTrack(id="t1", uri="uri1", name="S1", artists="A1"),
            PlaylistTrack(id="t2", uri="uri2", name="S2", artists="A2"),
        ]

        result = create_playlist(mock_client, "My Playlist", tracks)

        assert result is not None
        mock_client.user_playlist_create.assert_called_once()
        mock_client.playlist_add_items.assert_called_once()

    def test_create_playlist_empty_tracks(
        self, mock_client, sample_user, sample_playlist_response
    ):
        """Test creating playlist with no tracks."""
        mock_client.me.return_value = sample_user.model_dump()
        mock_client.user_playlist_create.return_value = (
            sample_playlist_response.model_dump()
        )

        result = create_playlist(mock_client, "Empty Playlist", [])

        assert result is not None
        mock_client.playlist_add_items.assert_not_called()


class TestAddTracksToPlaylist:
    """Tests for adding tracks to playlists."""

    def test_add_tracks_success(self, mock_client):
        """Test successful track addition."""
        result = add_tracks_to_playlist(
            mock_client, "playlist123", ["uri1", "uri2", "uri3"]
        )

        assert result is True
        mock_client.playlist_add_items.assert_called_once()

    def test_add_tracks_batches_large_lists(self, mock_client):
        """Test that large track lists are batched."""
        # Create 150 URIs (should be split into 2 batches)
        uris = [f"uri{i}" for i in range(150)]

        add_tracks_to_playlist(mock_client, "playlist123", uris)

        # Should be called twice (100 + 50)
        assert mock_client.playlist_add_items.call_count == 2

    def test_add_tracks_empty_list(self, mock_client):
        """Test adding empty list does nothing."""
        result = add_tracks_to_playlist(mock_client, "playlist123", [])

        assert result is True
        mock_client.playlist_add_items.assert_not_called()


class TestUpdatePlaylist:
    """Tests for playlist update functionality."""

    def test_update_playlist_adds_new_tracks(self, mock_client):
        """Test updating playlist with new tracks."""
        # Existing playlist with one track
        existing = Item(track=Track(
            id="existing1", name="Existing", uri="uri_existing", artists=[]
        ))
        playlist_resp = PlaylistResponse(
            id="playlist123",
            name="Test",
            tracks=Tracks(items=[existing], next=None, total=1),
        )
        mock_client.playlist.return_value = playlist_resp.model_dump()

        # New track to add
        new_tracks = [
            PlaylistTrack(id="new1", uri="uri_new1", name="New Song", artists="Artist")
        ]

        result = update_playlist(mock_client, "playlist123", new_tracks)

        assert len(result.tracks_added) == 1
        assert result.tracks_added[0].id == "new1"
        mock_client.playlist_add_items.assert_called_once()

    def test_update_playlist_skips_existing(self, mock_client):
        """Test that existing tracks are skipped."""
        existing = Item(track=Track(
            id="track1", name="Song 1", uri="uri1", artists=[]
        ))
        playlist_resp = PlaylistResponse(
            id="playlist123",
            name="Test",
            tracks=Tracks(items=[existing], next=None, total=1),
        )
        mock_client.playlist.return_value = playlist_resp.model_dump()

        # Try to add same track
        new_tracks = [
            PlaylistTrack(id="track1", uri="uri1", name="Song 1", artists="")
        ]

        result = update_playlist(mock_client, "playlist123", new_tracks)

        assert len(result.skipped_existing) == 1
        assert len(result.tracks_added) == 0

    def test_update_playlist_removes_old_when_max_exceeded(self, mock_client):
        """Test LIFO behavior when max_size is exceeded."""
        # Two existing tracks
        existing1 = Item(track=Track(
            id="old1", name="Old 1", uri="uri_old1", artists=[]
        ))
        existing2 = Item(track=Track(
            id="old2", name="Old 2", uri="uri_old2", artists=[]
        ))
        playlist_resp = PlaylistResponse(
            id="playlist123",
            name="Test",
            tracks=Tracks(items=[existing1, existing2], next=None, total=2),
        )
        mock_client.playlist.return_value = playlist_resp.model_dump()

        # Add 2 new tracks with max_size=3 (should remove 1 old)
        new_tracks = [
            PlaylistTrack(id="new1", uri="uri_new1", name="New 1", artists="A"),
            PlaylistTrack(id="new2", uri="uri_new2", name="New 2", artists="A"),
        ]

        result = update_playlist(
            mock_client, "playlist123", new_tracks, max_size=3
        )

        assert len(result.tracks_added) == 2
        assert len(result.tracks_removed) == 1
        # First track (oldest) should be removed
        assert result.tracks_removed[0].id == "old1"


class TestGetOrCreatePlaylist:
    """Tests for get_or_create_playlist."""

    def test_gets_existing_playlist(self, mock_client, sample_user):
        """Test finding an existing playlist by name."""
        mock_client.me.return_value = sample_user.model_dump()
        mock_client.user_playlists.return_value = {
            "items": [{"id": "found123", "name": "My Playlist"}],
            "next": None,
        }
        mock_client.playlist.return_value = {
            "id": "found123",
            "name": "My Playlist",
            "tracks": {"items": [], "next": None},
        }

        result = get_or_create_playlist(mock_client, "My Playlist")

        assert result is not None
        assert result.id == "found123"
        # Should not create new playlist
        mock_client.user_playlist_create.assert_not_called()

    def test_creates_new_when_not_found(self, mock_client, sample_user):
        """Test creating new playlist when not found."""
        mock_client.me.return_value = sample_user.model_dump()
        mock_client.user_playlists.return_value = {"items": [], "next": None}
        mock_client.user_playlist_create.return_value = {
            "id": "new123",
            "name": "New Playlist",
            "tracks": {"items": [], "next": None},
        }

        result = get_or_create_playlist(mock_client, "New Playlist")

        assert result is not None
        mock_client.user_playlist_create.assert_called_once()


class TestResolveTrackFromUrl:
    """Tests for resolve_track_from_url."""

    def test_resolve_track_url(self, mock_client, sample_track):
        """Test resolving a track from URL."""
        mock_client.track.return_value = sample_track.model_dump()

        result = resolve_track_from_url(
            mock_client, "https://open.spotify.com/track/track123"
        )

        assert result is not None
        assert result.id == "track123"
        assert result.name == "Test Song"

    def test_resolve_track_url_failure(self, mock_client):
        """Test handling invalid track URL."""
        mock_client.track.side_effect = Exception("Not found")

        result = resolve_track_from_url(mock_client, "invalid_url")

        assert result is None

