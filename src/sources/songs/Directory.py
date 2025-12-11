import os

from src.sources.SongSearchItem import SongSearchItem
from src.sources.songs.SongsSourceBase import SongsSourceBase
import mutagen


class Directory(SongsSourceBase):
    # File Types so search for in the SONG_SOURCE_DIRECTORY
    song_file_types = [".mp3", ".wav", ".m4a"]

    INPUT_PATH = []

    def __init__(self, user_args):
        if user_args.get("input_path"):
            self.INPUT_PATH += user_args["input_path"]
        if os.getenv("INPUT_DIRECTORY_PATH"):
            self.INPUT_PATH.append(os.getenv("INPUT_DIRECTORY_PATH"))

        if self.INPUT_PATH and not all([os.path.isdir(input_dir)] for input_dir in self.INPUT_PATH):
            self.raise_error(f'{self.INPUT_PATH} is not a valid directory. Exiting...')

        super().__init__(user_args)

    @staticmethod
    def is_applicable(user_args: dict) -> bool:
        return bool(user_args.get("input_path") or os.getenv("INPUT_DIRECTORY_PATH"))

    def get_song_list(self) -> list[str]:
        search_list = []
        for source_directory in self.INPUT_PATH:
            # Get songs from SONG_SOURCE_DIRECTORY and clean those songs from unwanted words and characters
            search_list += self.clean_search_list(
                self._parse_songs_from_directory(directory=source_directory, filetypes=self.song_file_types))

        return search_list

    # Parses the SONG_SOURCE_DIRECTORY for songs with filetype from SONG_SOURCE_DIRECTORY
    @staticmethod
    def _parse_songs_from_directory(directory: str, filetypes: list) -> list[SongSearchItem]:
        songs = []

        # Check any songs that have the song name and artist set in metadata tags
        remaining_files = []
        for file in os.listdir(directory):
            if not os.path.isfile(os.path.join(directory, file)):
                continue
            if os.path.splitext(file)[1] in filetypes:
                audio = mutagen.File(os.path.join(directory, file), easy=True)
                if audio is not None:
                    title = audio.get('title', [None])[0]
                    artist = audio.get('artist', [None])[0]
                    if title and artist:
                        songs.append(SongSearchItem(name_tag=(title,), artist_tag=(artist,)))
                    else:
                        remaining_files.append(file)

        # Create list with all song names and check for correct file types
        # The encoding and decoding is done to prevent an error
        parsed_songs = [os.path.splitext(file)[0].encode("utf-8").decode('utf-8', 'ignore') for file in
                        remaining_files if os.path.splitext(file)[1] in filetypes]

        songs += [SongSearchItem(name_tag=song) for song in parsed_songs]

        print(f"Successfully parsed all songs from {directory}")

        return songs