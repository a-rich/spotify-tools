import os
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from typing import Optional

from spotify_tools.client import Client
from spotify_tools.schemas import Track, TrackSearchResults


class SearchType(Enum):
    ALBUM = "album"
    ARTIST = "artist"
    EPISODE = "episode"
    PLAYLIST = "playlist"
    SHOW = "show"
    TRACK = "track"
    

def search(
    client: Client,
    track: str,
    artist: Optional[str] = None,
    ambiguous_order: bool = False,
    limit: int = 50,
    search_type: SearchType = SearchType.TRACK,
) -> list[Track]
    q_template = "track:{track}"

    if artist:
        q_template += " artist:{artist}"
    
    queries = [q_template.format(track=track, artist=artist)]

    if ambiguous_order:
        queries.append(q_template.format(track=artist, artist=track))
    
    args_list = [{"q": query, "limit": limit, "type": search_type} for query in queries)]

    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        tracks = []
        results = [executor.map(client.search, args) for args in args_list]
        for result in results:
            tracks.extend(
                TrackSearchResults.model_validate(result["tracks"])
            )

    breakpoint()