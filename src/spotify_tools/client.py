from spotipy2 import Spotify
from spotipy2.auth import OauthFlow

from spotify_tools.schemas import SpotifyConfig


DEFAULT_SCOPES = [
    "playlist-read-private",
    "playlist-read-collaborative",
    "playlist-modify-private",
    "playlist-modify-public",
    "user-read-private",
]


class Client(Spotify):
    def __init__(self, *args, config: SpotifyConfig, **kwargs) -> "Client":
        auth_flow = OauthFlow(
            client_id=config.CLIENT_ID,
            client_secret=config.CLIENT_SECRET,
            redirect_uri=config.REDIRECT_URI,
            scope=DEFAULT_SCOPES,
            open_browser=True,
        )
        self._redirect_callback = auth_flow.get_redirect
        super().__init__(*args, auth_flow=auth_flow, **kwargs)

    async def _auth_startup(self) -> None:
        await self._redirect_callback()

    @classmethod
    async def create(cls, *args, config: SpotifyConfig, **kwargs) -> "Client":
        self = cls(*args, config=config, **kwargs)
        await self._auth_startup()

        return self
