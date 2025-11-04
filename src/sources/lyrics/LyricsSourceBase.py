import os
import sys
from abc import ABCMeta, abstractmethod

from src.sources.SongSearchItem import SongSearchItem


class LyricsSourceBase(metaclass=ABCMeta):
    OUTPUT_DIRECTORY = ""
    def __init__(self, user_args: dict):
        self.OUTPUT_DIRECTORY = user_args["output_path"] or os.getenv("OUTPUT_DIRECTORY")

    @staticmethod
    def raise_error(err_massage: str):
        print(err_massage)
        sys.exit(1)

    @abstractmethod
    def _execute_search(self, artist_string: str, title_string: str) -> list[list]:
        return []
    
    @abstractmethod
    def download_all_lyrics(self, song_list: list) -> list[str]:
        pass
    
    def native_search(self, search_list: list, find_all_matching: bool) -> list[list]:
        song_list = []

        for count, search_item in enumerate(search_list):
            search_result = self._execute_search_for_search_item(search_item=search_item)
            if not search_result: continue

            song_list += search_result

            if not find_all_matching:
                search_list.pop(count)

        return song_list

    # Create the payload to login on http://usdb.animux.de/ with the user data
    def _create_search_payload(self, interpret: str = "", title: str = "", edition: str = "", language: str = "",
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

    def _execute_search_for_search_item(
            self,
            search_item: SongSearchItem,
    ) -> list[list]:
        artist_string = " ".join(search_item.artist_tag_tuple)
        title_string = " ".join(search_item.name_tag_tuple)

        search_results = self._execute_search(artist_string=artist_string, title_string=title_string)

        if search_results:
            return search_results

        has_multiple_artists = len(search_item.artist_tag_tuple) > 1
        if has_multiple_artists:
            print(f"Could not find any results for {search_item}. Retrying with artists separated")

            for artist in search_item.artist_tag_tuple:
                search_results = self._execute_search(artist_string=artist, title_string=title_string)

                if search_results:
                    return search_results

        return []

