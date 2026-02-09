import os

from src.sources.ColorPrint import ColorPrint
from src.sources.songs.SongsSourceBase import SongsSourceBase
from src.sources.SongSearchItem import SongSearchItem
from ..utils import list_or_empty


class File(SongsSourceBase):

    INPUT_FILE = []
    def __init__(self, user_args):
        self.INPUT_FILE = user_args["inputTextfile"] or list_or_empty(os.getenv("INPUT_FILE_PATH"))

    def get_song_list(self) -> list[str]:
        search_list = []
        for textfile in self.INPUT_FILE:
            if not os.path.isfile(textfile):
                ColorPrint.print(ColorPrint.FAIL, f"File {textfile} does not exist. Skipping...")
                continue
            search_list += [line.try_separate() for line in self._parse_songs_from_textfile(path=textfile)]

        return search_list

    @staticmethod
    def _parse_songs_from_textfile(path: str) -> list[SongSearchItem]:
        with open(file=path, mode="r") as f:
            entries = f.read().splitlines()

        parsed_objects = [SongSearchItem(name_tag=song) for song in entries]

        return parsed_objects
