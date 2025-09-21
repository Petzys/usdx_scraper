import os
import sys

import requests

from src.sources.SongSearchItem import SongSearchItem


class LyricsSourceBase:
    OUTPUT_DIRECTORY = ""
    def __init__(self, user_args: dict):
        self.OUTPUT_DIRECTORY = user_args["output_path"] or os.getenv("OUTPUT_DIRECTORY")

    @staticmethod
    def raise_error(err_massage: str):
        print(err_massage)
        sys.exit(1)

    def native_search(self, search_list: list, find_all_matching: bool) -> list[list]:
        return []

    def execute_search(self, artist_string: str, title_string: str) -> list[list]:
        return []

    def create_cookies(self, song_list: list) -> list:
        return []

    def create_login_payload(self, user: str, password: str) -> dict[str, str]:
        return {}

    def get_yt_url(self, song: str, id: str) -> str:
        return ""

    # Create the payload to login on http://usdb.animux.de/ with the user data
    def create_search_payload(self, interpret: str = "", title: str = "", edition: str = "", language: str = "",
                              genre: str = "", user: str = "", order: str = "", ud: str = "", limit: int = 100,
                              start: int = 0, ) -> dict[str, str | int]:
        return {
            'interpret': interpret,
            'title': title,
            'edition': edition,
            'language': language,
            'genre': genre,
            'user': user,
            'order': order,
            'ud': ud,
            'limit': limit,
        }

    def execute_search_for_search_item(
            self,
            search_item: SongSearchItem,
    ) -> list[list]:
        artist_string = " ".join(search_item.artist_tag_tuple)
        title_string = " ".join(search_item.name_tag_tuple)

        search_results = self.execute_search(artist_string=artist_string, title_string=title_string)

        if search_results:
            return search_results

        has_multiple_artists = len(search_item.artist_tag_tuple) > 1
        if has_multiple_artists:
            print(f"Could not find any results for {search_item}. Retrying with artists separated")

            for artist in search_item.artist_tag_tuple:
                search_results = self.execute_search(artist_string=artist, title_string=title_string)

                if search_results:
                    return search_results

        return []

    def download_lyrics(self, cookie: str, download_url: str, directory: str) -> str:
        return ""

