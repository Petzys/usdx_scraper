import re


class SongSearchItem:
    def __init__(self, name_tag, artist_tag=tuple()):
        self.artist_tag_tuple = artist_tag if isinstance(artist_tag, tuple) else tuple([artist_tag])
        self.name_tag_tuple = name_tag if isinstance(name_tag, tuple) else tuple([name_tag])

    def __key(self):
        return self.artist_tag_tuple + self.name_tag_tuple

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        if isinstance(other, SongSearchItem):
            return self.__key() == other.__key()
        return NotImplemented

    def __str__(self):
        return f"Search item: artists={self.artist_tag_tuple}; names={self.name_tag_tuple}"

    def __repr__(self):
        return f"Search item: artists={self.artist_tag_tuple}; names={self.name_tag_tuple}"

    def __len__(self) -> int:
        return len(self.artist_tag_tuple) + len(self.name_tag_tuple)

    def clean_up(self, ignored_pattern: str):
        self.name_tag_tuple = tuple(
            [re.sub(r'[^a-zA-Z0-9\s]|(%s)' % ignored_pattern, '', self.ignore_brackets(tag), re.IGNORECASE) for tag in
             self.name_tag_tuple])
        self.artist_tag_tuple = tuple(
            [re.sub(r'[^a-zA-Z0-9\s]|(%s)' % ignored_pattern, '', self.ignore_brackets(tag), re.IGNORECASE) for tag in
             self.artist_tag_tuple])

        self.name_tag_tuple = tuple(
            [re.sub(r'^\s+|\s+$', '', tag) for tag in self.name_tag_tuple if not re.match(r"^[ 0-9]+$", tag)])
        self.artist_tag_tuple = tuple(
            [re.sub(r'^\s+|\s+$', '', tag) for tag in self.artist_tag_tuple if not re.match(r"^[ 0-9]+$", tag)])

    def try_separate(self):
        # Abort if more than one item in name_tag_set
        tag_list = list(self.name_tag_tuple)
        if len(tag_list) > 1:
            return self
        elif "-" in tag_list[0]:
            s = tag_list[0].split("-")

            artist_tag_tuple = tuple(s[:-1])
            self.artist_tag_tuple = self.strip(artist_tag_tuple)

            name_tag_tuple = tuple(s[-1:])
            self.name_tag_tuple = self.strip(name_tag_tuple)

            return self
        else:
            return self

    def get_list(self) -> list:
        return list(self.name_tag_tuple) + list(self.artist_tag_tuple)

    @staticmethod
    def strip(tags):
        return tuple(tag.strip() for tag in tags)

    # Function to ignore the content of brackets
    @staticmethod
    def ignore_brackets(s):
        s = re.sub(r'\(.*?\)', '', s)
        s = re.sub(r'\[.*?\]', '', s)
        s = re.sub(r'\{.*?\}', '', s)
        return s