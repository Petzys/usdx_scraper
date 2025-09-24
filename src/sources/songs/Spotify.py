import os

import spotipy
from spotipy import SpotifyClientCredentials

from .SongsSourceBase import SongsSourceBase
from ..SongSearchItem import SongSearchItem


class Spotify(SongsSourceBase):

    CLIENT_ID = ""
    CLIENT_SECRET = ""
    PLAYLIST_ID = []

    def __init__(self, user_args):
        self.CLIENT_ID = user_args["spotify_id"] or os.getenv("SPOTIPY_CLIENT_ID")
        self.CLIENT_SECRET = user_args["spotify_secret"] or os.getenv("SPOTIPY_CLIENT_SECRET")
        self.PLAYLIST_ID = user_args["spotify_input"] or os.getenv("SPOTIPY_PLAYLIST_ID")

        if self.PLAYLIST_ID and not (self.CLIENT_ID and self.CLIENT_SECRET): self.raise_error(
            "Client ID and secret are required if a Spotify playlist is specified")

        super().__init__()



    def get_song_list(self) -> list[str]:
        playlist_tracks = self.get_all_tracks()
        search_list = []
        for track in playlist_tracks:
            track = track["track"]
            artist_set = tuple([artist["name"] for artist in track["artists"]])
            name_set = tuple([track["name"]])
            item = SongSearchItem(name_set, artist_set)
            search_list.append(item)

        print(f"Successfully got parsed playlist from Spotify: {self.PLAYLIST_ID}")
        return search_list


    def get_all_tracks(self):
        auth_manager = SpotifyClientCredentials(self.CLIENT_ID, self.CLIENT_SECRET)
        spotify_client = spotipy.Spotify(auth_manager=auth_manager)
        playlist_identifier = self.PLAYLIST_ID

        tracks = []
        offset = 0
        limit = 100

        while True:
            print(f"Query Tracks {offset} to {offset + limit}")
            playlist = spotify_client.playlist_items(
                playlist_id=playlist_identifier,
                fields="items(track(name,artists(name)))",
                offset=offset,
                limit=limit
            )
            items = playlist["items"]

            if not items:
                break

            tracks.extend(items)
            offset += limit

        return tracks