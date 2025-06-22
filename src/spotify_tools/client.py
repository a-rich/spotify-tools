from spotipy2 import Spotify
from spotipy2.auth import OauthFlow

from spotify_tools.schemas import SpotifyConfig


class Client(Spotify):
    def __init__(self, *args, config: SpotifyConfig, **kwargs):
        auth_flow = OauthFlow(
            client_id=config.CLIENT_ID,
            client_secret=config.CLIENT_SECRET,
            redirect_uri=config.REDIRECT_URI,
            scope="playlist-modify-private playlist-modify-public",
            # requests_timeout=30,
            # cache_handler=spotipy.CacheFileHandler(
            #     cache_path=Path(__file__).parent / ".spotipy.cache"
            # ),
        )
        super().__init__(*args, auth_flow=auth_flow, **kwargs)
