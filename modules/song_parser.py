import os
import re
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from modules import config
import logging

logger = logging.getLogger(__name__)

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
        return f"SearchItem={self.artist_tag_tuple}{self.name_tag_tuple}"

    def __repr__(self):
        return f"SearchItem={self.artist_tag_tuple}{self.name_tag_tuple}"

    def __len__(self) -> int:
        return len(self.artist_tag_tuple) + len(self.name_tag_tuple)

    def clean_up(self, IGNORED_PATTERN:list):
        self.name_tag_tuple = tuple([re.sub(r'[^a-zA-Z0-9\s]|(%s)' % IGNORED_PATTERN, '', ignore_brackets(tag), re.IGNORECASE) for tag in self.name_tag_tuple])
        self.artist_tag_tuple = tuple([re.sub(r'[^a-zA-Z0-9\s]|(%s)' % IGNORED_PATTERN, '', ignore_brackets(tag), re.IGNORECASE) for tag in self.artist_tag_tuple])

        self.name_tag_tuple = tuple([re.sub(r'^\s+|\s+$', '', tag) for tag in self.name_tag_tuple if not re.match(r"^[ 0-9]+$", tag)])
        self.artist_tag_tuple = tuple([re.sub(r'^\s+|\s+$', '', tag) for tag in self.artist_tag_tuple if not re.match(r"^[ 0-9]+$", tag)])

    def try_separate(self):
        # Abort if more than one item in name_tag_set
        tag_list = list(self.name_tag_tuple)
        if len(tag_list)>1: 
            return self
        elif "-" in tag_list[0]:
            s = tag_list[0].split("-")
            self.artist_tag_tuple = tuple(s[:-1])
            self.name_tag_tuple = tuple(s[-1:])
            return self
        else:
            return self

    def get_list(self) -> list:
        return list(self.name_tag_tuple)+list(self.artist_tag_tuple)
    
##### Directory Parsing #####

# Parses the SONG_SOURCE_DIRECTORY for songs with filetype from SONG_SOURCE_DIRECTORY
def parse_songs_from_directory(directory:str, filetypes:list) -> list[SongSearchItem]:
    # Create list with all song names and check for correct file types
    # The encoding and decoding is done to prevent an error
    parsed_songs = [os.path.splitext(file)[0].encode("utf-8").decode('utf-8','ignore') for file in os.listdir(directory) if os.path.splitext(file)[1] in filetypes]

    parsed_objects = [SongSearchItem(name_tag=song) for song in parsed_songs]
    
    logger.info(f"Successfully parsed all songs from {directory}")

    return parsed_objects

# Function to ignore the content of brackets
def ignore_brackets(s):
    s = re.sub(r'\(.*?\)', '', s)
    s = re.sub(r'\[.*?\]', '', s)
    s = re.sub(r'\{.*?\}', '', s)
    return s

# Strip all entries of the search list from unwanted additions from the ignored_words
def clean_search_list(search_list:list[SongSearchItem]) -> list[SongSearchItem]:
    
    for item in search_list:
        item.try_separate()
        item.clean_up(config.IGNORED_PATTERN)
    
    # delete all entries with are only one entry (to prevent false matching later)
    search_list = [item for item in search_list if len(item)>1]
    logger.info(f"Successfully stripped search list")
    return (search_list)

##### Spotify Parsing #####

def parse_songs_from_spotify(client_id:str, client_secret:str, playlist_identifier:str) -> list[SongSearchItem]:
    spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))

    playlist = spotify.playlist_items(playlist_id=playlist_identifier, fields="items(track(name,artists(name)))")
    search_list = []
    for track in playlist["items"]:
        track = track["track"]
        artist_set = tuple([artist["name"] for artist in track["artists"]])
        name_set = tuple([track["name"]])
        item = SongSearchItem(name_set, artist_set)
        search_list.append(item)

    logger.info(f"Successfully got parsed playlist from Spotify: {playlist_identifier}")
    return search_list

##### Textfile Parsing #####

def parse_songs_from_textfile(path:str) -> list[SongSearchItem]:
    with open(file=path, mode="r") as f:
        entries = f.read().splitlines()

    parsed_objects = [SongSearchItem(name_tag=song) for song in entries]

    for item in parsed_objects:
        item.try_separate()

    return parsed_objects

