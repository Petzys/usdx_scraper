import os

from src.sources.SongSearchItem import SongSearchItem
from src.sources.songs.SongsSourceBase import SongsSourceBase


class File(SongsSourceBase):

    INPUT_FILE = ""
    def __init__(self, user_args):
        self.INPUT_FILE = user_args["inputTextfile"] or os.getenv("INPUT_FILE_PATH")
        if self.INPUT_FILE and not all(
            [os.path.isfile(file)] for file in self.INPUT_FILE): self.raise_error(
            f'{self.INPUT_FILE} is not a valid file. Exiting...')


    def get_song_list(self) -> list[str]:
        search_list = []
        for textfile in self.INPUT_FILE:
            search_list += [line.try_separate() for line in self.parse_songs_from_textfile(path=textfile)]

        return search_list

    @staticmethod
    def parse_songs_from_textfile(path: str) -> list[SongSearchItem]:
        with open(file=path, mode="r") as f:
            entries = f.read().splitlines()

        parsed_objects = [SongSearchItem(name_tag=song) for song in entries]

        return parsed_objects
