from typing import Optional


from pydantic import BaseModel, NonNegativeInt, PositiveInt
from pydantic_settings import BaseSettings, SettingsConfigDict


###############################################################################
# Schemas for spotify-tools configs
###############################################################################


class SpotifyConfig(BaseSettings):
    CLIENT_ID: str = ""
    CLIENT_SECRET: str = ""
    PLAYLIST_ID: str = ""
    REDIRECT_URI: str = ""

    model_config = SettingsConfigDict(env_prefix="SPOTIFY_TOOLS_")


###############################################################################
# Schemas for validating spotipy's "playlist" response
# https://spotipy.readthedocs.io/en/2.25.1/#spotipy.client.Spotify.playlist
###############################################################################


class ExternalUrls(BaseModel):
    spotify: Optional[str] = None


class Followers(BaseModel):
    href: Optional[str] = None
    total: Optional[NonNegativeInt] = None


class Image(BaseModel):
    height: Optional[NonNegativeInt] = None
    url: Optional[str] = None
    width: Optional[NonNegativeInt] = None


class Owner(BaseModel):
    display_name: Optional[str] = None
    external_urls: Optional[ExternalUrls] = None
    href: Optional[str] = None
    id: Optional[str] = None
    type: Optional[str] = None
    uri: Optional[str] = None


class User(BaseModel):
    display_name: Optional[str] = None
    external_urls: Optional[ExternalUrls] = None
    followers: Optional[Followers] = None
    href: Optional[str] = None
    id: Optional[str] = None
    images: Optional[list[Image]] = None
    type: Optional[str] = None
    uri: Optional[str] = None


class AddedBy(BaseModel):
    external_urls: Optional[ExternalUrls] = None
    href: Optional[str] = None
    id: Optional[str] = None
    type: Optional[str] = None
    uri: Optional[str] = None


class Artist(BaseModel):
    external_urls: Optional[ExternalUrls] = None
    href: Optional[str] = None
    id: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    uri: Optional[str] = None


class Album(BaseModel):
    available_markets: Optional[list[str]] = None
    type: Optional[str] = None
    album_type: Optional[str] = None
    href: Optional[str] = None
    id: Optional[str] = None
    images: Optional[list[Image]] = None
    name: Optional[str] = None
    release_date: Optional[str] = None
    release_date_precision: Optional[str] = None
    uri: Optional[str] = None
    artists: Optional[list[Artist]] = None
    external_urls: Optional[ExternalUrls] = None
    total_tracks: Optional[NonNegativeInt] = None


class ExternalIds(BaseModel):
    isrc: Optional[str] = None


class Track(BaseModel):
    # preview_url: Optional["NoneType"] = None
    available_markets: Optional[list[str]] = None
    explicit: Optional[bool] = None
    type: Optional[str] = None
    episode: Optional[bool] = None
    track: Optional[bool] = None
    album: Optional[Album] = None
    artists: Optional[list[Artist]] = None
    disc_number: Optional[NonNegativeInt] = None
    track_number: Optional[NonNegativeInt] = None
    duration_ms: Optional[PositiveInt] = None
    external_ids: Optional[ExternalIds] = None
    external_urls: Optional[ExternalUrls] = None
    href: Optional[str] = None
    id: Optional[str] = None
    name: Optional[str] = None
    popularity: Optional[NonNegativeInt] = None
    uri: Optional[str] = None
    is_local: Optional[bool] = None


class VideoThumbnail(BaseModel):
    uri: Optional[str] = None


class Item(BaseModel):
    added_at: Optional[str] = None
    added_by: Optional[AddedBy] = None
    is_local: Optional[bool] = None
    # primary_color: Optional["NoneType"] = None
    track: Optional[Track] = None
    video_thumbnail: Optional[VideoThumbnail] = None


class Tracks(BaseModel):
    href: Optional[str] = None
    items: Optional[list[Item]] = None
    limit: Optional[NonNegativeInt] = None
    next: Optional[str] = None
    offset: Optional[NonNegativeInt] = None
    # previous: Optional["NoneType"] = None
    total: Optional[NonNegativeInt] = None


class PlaylistResponse(BaseModel):
    """Response object returned by Spotipy client's 'playlist' method."""

    collaborative: Optional[bool] = None
    description: Optional[str] = None
    external_urls: Optional[ExternalUrls] = None
    followers: Optional[Followers] = None
    href: Optional[str] = None
    id: Optional[str] = None
    images: Optional[list[Image]] = None
    name: Optional[str] = None
    owner: Optional[Owner] = None
    # primary_color: Optional["NoneType"] = None
    public: Optional[bool] = None
    snapshot_id: Optional[str] = None
    tracks: Optional[Tracks] = None
    type: Optional[str] = None
    uri: Optional[str] = None


###############################################################################
# Schemas for validating spotipy's "search" response
# https://spotipy.readthedocs.io/en/2.25.1/#spotipy.client.Spotify.search
###############################################################################


class TrackSearchResults(BaseModel):
    href: Optional[str] = None
    items: Optional[list[Track]] = None
    limit: Optional[NonNegativeInt] = None
    next: Optional[str] = None
    offset: Optional[NonNegativeInt] = None
    total: Optional[NonNegativeInt] = None
