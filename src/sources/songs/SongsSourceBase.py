import sys

from src.sources.SongSearchItem import SongSearchItem


class SongsSourceBase:
    # All words to ignore in file names
    ignored_words = ['Official', 'Video', 'ft', 'feat', 'Music', 'Lyrics', 'the', 'stereo', 'mono', 'instrumental',
                     'cover', 'Lyric', 'Remix', '_', 'Audio',
                     'Live', 'Version', 'Performance', 'Session', 'Acoustic', 'Remastered', 'HD', 'HQ', 'Edit', 'Mix',
                     'Cover', 'Tribute', 'Mashup', 'Bootleg', 'Concert',
                     'Version', 'Studio', 'Orchestra', 'Band', 'Official', 'Audio', 'Video', 'lyrics', 'extended',
                     'full', 'dance', 'remake', 'reprise', 'reinterpretation',
                     'piano', 'guitar', 'violin', 'cello', 'saxophone', 'flute', 'drum', 'bass', 'instrumental', "Duet",
                     "Duett"]
    ignored_pattern = "|".join(ignored_words)

    @staticmethod
    def raise_error(err_massage: str):
        print(err_massage)
        sys.exit(1)

    def get_song_list(self) -> list[str]:
        return []

    # Strip all entries of the search list from unwanted additions from the ignored_words
    def clean_search_list(self, search_list: list[SongSearchItem]) -> list[SongSearchItem]:
        for item in search_list:
            item.try_separate()
            item.clean_up(self.ignored_pattern)

        # delete all entries with are only one entry (to prevent false matching later)
        search_list = [item for item in search_list if len(item) > 1]
        print(f"Successfully stripped search list")
        return search_list