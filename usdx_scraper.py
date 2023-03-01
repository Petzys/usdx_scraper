import requests, zipfile, io, os, sys, argparse, re, shutil
from requests.adapters import HTTPAdapter, Retry
import spotipy
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from youtubesearchpython import VideosSearch
from pytube import YouTube
from spotipy.oauth2 import SpotifyClientCredentials

# General
LOGIN_URL = 'https://usdb.animux.de/index.php?&link=login'
SONG_URL = 'https://usdb.animux.de/index.php?link=detail&id='
ZIP_URL = 'https://usdb.animux.de/index.php?&link=ziparchiv'
ZIP_SAVE_URL = 'https://usdb.animux.de/index.php?&link=ziparchiv&save=1'
DOWNLOAD_URL = "https://usdb.animux.de/data/downloads"

# Path to the HTML File containing all database links
DATABASE_URL = "https://usdb.hehoe.de/"
DATABASE_HTML = "Index of all UltraStar songs available in databases.htm"

# File Types so search for in the SONG_SOURCE_DIRECTORY
SONG_FILE_TYPES = [".mp3", ".wav", ".m4a"]

# All words to ignore in file names
ignored_words = ['Official', 'Video', 'ft', 'feat', 'Music', 'Lyrics', 'the', 'stereo', 'mono', 'instrumental', 'cover', 'Lyric', 'Remix', '_', 'Audio',
                 'Live', 'Version', 'Performance', 'Session', 'Acoustic', 'Remastered', 'HD', 'HQ', 'Edit', 'Mix', 'Cover', 'Tribute', 'Mashup', 'Bootleg', 'Concert',
                 'Version', 'Studio', 'Orchestra', 'Band', 'Official', 'Audio', 'Video', 'lyrics', 'extended', 'full', 'dance', 'remake', 'reprise', 'reinterpretation',
                 'piano', 'guitar', 'violin', 'cello', 'saxophone', 'flute', 'drum', 'bass', 'instrumental', "Duet", "Duett"]
ignored_pattern = ("|").join(ignored_words)

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

    def clean_up(self, ignored_pattern:list):
        self.name_tag_tuple = tuple([re.sub(r'[^a-zA-Z0-9\s]|(%s)' % ignored_pattern, '', ignore_brackets(tag), re.IGNORECASE) for tag in self.name_tag_tuple])
        self.artist_tag_tuple = tuple([re.sub(r'[^a-zA-Z0-9\s]|(%s)' % ignored_pattern, '', ignore_brackets(tag), re.IGNORECASE) for tag in self.artist_tag_tuple])

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

def raise_error(err_massage:str):
    print(err_massage)
    sys.exit(1)

# Parses the SONG_SOURCE_DIRECTORY for songs with filetype from SONG_SOURCE_DIRECTORY
def parse_songs_from_directory(directory:str, filetypes:list) -> list[SongSearchItem]:
    # Create list with all song names and check for correct file types
    # The encoding and decoding is done to prevent an error
    parsed_songs = [os.path.splitext(file)[0].encode("utf-8").decode('utf-8','ignore') for file in os.listdir(directory) if os.path.splitext(file)[1] in filetypes]

    parsed_objects = [SongSearchItem(name_tag=song) for song in parsed_songs]
    
    print(f"Successfully parsed all songs from {directory}")

    return parsed_objects

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

    print(f"Successfully got parsed playlist from Spotify: {playlist_identifier}")
    return search_list

def parse_songs_from_textfile(path:str) -> list[SongSearchItem]:
    with open(file=path, mode="r") as f:
        entries = f.read().splitlines()

    parsed_objects = [SongSearchItem(name_tag=song) for song in entries]

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
        item.clean_up(ignored_pattern)
    
    # delete all entries with are only one entry (to prevent false matching later)
    search_list = [item for item in search_list if len(item)>1]
    print(f"Successfully stripped search list")
    return (search_list)

def get_html_database(url:str, output:str):
    response = requests.get(url)

    if not response.ok: raise_error("Failed to get HTML Database")
    with open(output, "w", encoding='utf-8') as file:
        file.write(response.text)

    return

# Iterate through all links to songs in the HTML database and check for search_list items
def search_html_database(html:str, search_list:list[SongSearchItem], find_all_matching:bool) -> list[list]:
    song_list = [];

    with open(html, 'r', encoding='utf-8') as input:
        html_soup = BeautifulSoup(input, 'html5lib')
        # Only look for URLs redirecting to http://usdb.animux.de/
        regex_href = re.compile('usdb\.animux')
        
        # Iterate through all <a> tags with href attr.
        for track in html_soup.find("body").find_all("a",attrs={"href" : True}):
            # Skip if not from http://usdb.animux.de/
            if not re.search(regex_href, str(track.get('href'))): continue
            href = track.get('href')
            title = str(track.get("title"))

            for count, search_item in enumerate(search_list):
                # If all items from search_item are in title -> get this song
                if all((item.lower() in title.lower()) for item in search_item.get_list()):
                    print(f"Found match: {search_item} -> {title}")
                    # Append only the id of the song to later download
                    song_list.append([parse_qs(urlparse(href).query)['id'][0], title]);
                    # Delete this entry of the search_list
                    if not find_all_matching: search_list.pop(count)
                    break;
    
    print(f'Found {len(song_list)} matching songs')
    return song_list

# Create a list of cookies which contain all song IDs
def create_cookies(song_list:list) -> list:
    cookie_list = []
    i = 0
    for song in song_list:
        cookie_list.append("")
        cookie_part = song[0] + "|"
        cookie_list[i] += cookie_part
        i += 1

    return cookie_list

# Create the payload to login on http://usdb.animux.de/ with the user data
def create_payload(user:str, password:str) -> str:
    return {
        'user': user,
        'pass': password,
        'login': 'Login'
    }

# Create personal download URL for http://usdb.animux.de/
def create_personal_download_url(user:str) -> str:
    return f"{DOWNLOAD_URL}/{user}'s%20Playlist.zip"

# Download all Textfiles for USDX from http://usdb.animux.de/
def download_usdb_txt(payload:str, cookie:str, download_url:str, directory:str) -> str:
    with requests.Session() as session:

        retries = Retry(total=5, backoff_factor=1, status_forcelist=[ 502, 503, 504 ])
        session.mount('https://', HTTPAdapter(max_retries=retries))

        response = session.post(LOGIN_URL, data=payload)

        if "Login or Password invalid, please try again." in response.text:
            raise Exception("Could not authenticate");

        # Use the websites cookies to trick the site into putting all of the IDs into one download ZIP
        session.cookies.set('counter', '1');
        session.cookies.set('ziparchiv', cookie);

        # An authorized request.
        r = session.get(ZIP_URL)
        if not r.ok: raise ConnectionError
        r = session.get(ZIP_SAVE_URL)
        if not r.ok: raise ConnectionError
        r = session.get(download_url)
        if not r.ok: raise ConnectionError
        
        # Get ZIP and unpack
        z = zipfile.ZipFile(io.BytesIO(r.content))
        filename, _ = os.path.split(z.namelist()[0])
        z.extractall(directory)

    return filename

# Validate all the flags in a txt file and overwrite all that are different to the parameter
def validate_txt_tags(file_path:str, tags:dict[str, str]):
    # First read all the lines and get current tags
    current_tags = {}
    with open(file_path, 'r', encoding='cp1252') as file:
        lines = file.readlines();
        # Create dict with tag as key and value as value
        current_tags = {line.split(":")[0][1:]:line.split(":")[1] for line in lines if line.startswith("#")}
        content = lines[len(current_tags):]

    # Merge both dicts, tags is dominant and overwrites current_tags if keys match
    new_tags = current_tags | tags

    # Write all new tags to the file and append rest of file
    with open(file_path, 'w',  encoding='utf-8') as file:
        file.writelines([f"#{key}:{value}" for key,value in new_tags.items()])
        file.writelines(content)

# Rename all tags in the txt files to match the files in the directory
def clean_tags(songs_directory:str, song_folder:str):
    tags = {}
    files = os.listdir(os.path.join(songs_directory, song_folder))
    for file in files:
        # Set the tags to set with validate_txt_tags()
        filetype = os.path.splitext(file)[-1]
        match filetype:
            case ".mp3":
                tags["MP3"] = f"{file}\n"
                tags["VIDEO"] = f"{file}\n"
            case ".jpg":
                tags["COVER"] = f"{file}\n"
            case ".txt":
                txt = file
    validate_txt_tags(os.path.join(songs_directory, song_folder, txt), tags)

# Get all YouTube URLs: Either from the entry at SONG_URL or via YouTube search
def get_yt_url(song:str, id:str) -> str:
    # Try to find if there a link to a YT video on the songs http://usdb.animux.de/ page
    r = requests.get(SONG_URL+id)
    if not r.ok: raise Exception("GET failed")

    song_soup = BeautifulSoup(r.text, 'html5lib')

    yt_pattern = re.compile(r'youtu')
    a_tag = song_soup.find("a", href=yt_pattern)
    iframe = song_soup.find("iframe", src=yt_pattern)

    if iframe:
        # Get YT Video ID from embedded link and construct video url
        embed_link = iframe.get("src")
        video_id = embed_link.split("/")[-1]
        return f"https://www.youtube.com/watch?v={video_id}"
    elif a_tag: 
        # If a_tag to vt video is set, use this
        return a_tag.get("href")
    else:
        # Search for videos on YT and add links to song_list
        search_key = re.sub(r"\s*\([Dd][Uu][Ee][Tt]\)\s*|\s*\[[Dd][Uu][Ee][Tt]\]\s*|\s*\{[Dd][Uu][Ee][Tt]\}\s*|\s*[Dd][Uu][Ee][Tt]\s*", "", song)
        print(f"Searching for: {search_key} Music Video")
        videosSearch = VideosSearch(f'{search_key} Music Video', limit = 1)
        return videosSearch.result()["result"][0]["link"]

# Download all the songs and rename the folders to the correct song names from song_list
def download_song(song:str, folder:str, songs_directory:str, url:str) -> str:

    yt = YouTube(url)
    stream = yt.streams.filter(only_audio=False, file_extension="mp4").first()

    # Rename folders
    desired_path = os.path.join(songs_directory, song)

    if os.path.isdir(desired_path):
        #print(f"Tried to rename but folder already exists! Keeping old names... {desired_path}")
        desired_path = os.path.join(songs_directory, folder)
        song = folder
    elif os.path.isdir(os.path.join(songs_directory, folder)):
        os.rename(os.path.join(songs_directory, folder), desired_path)
    else: 
        print(f"Could not find directory {os.path.join(songs_directory, folder)}")
        raise FileNotFoundError
    
    for file in os.listdir(desired_path):
        file_ending = os.path.splitext(file)[-1]
        if os.path.isfile(os.path.join(desired_path, file)):
            os.rename(os.path.join(desired_path, file), os.path.join(desired_path, f"{song}{file_ending}")) 
        else:
            print(f"Could not find file {os.path.join(desired_path, file)}")
            raise FileNotFoundError

    # Download the files, age-restricted or else will be skipped
    out_file = stream.download(output_path=desired_path, filename=f'{song}.mp3', skip_existing=True)
        
    return song

def remove_duplicates(directory:str, song_list:str) -> list[list]:
    if not os.path.isdir(directory): return song_list
    files_in_directory = os.listdir(directory)
    return [song for song in song_list if song[1] not in files_in_directory]

def parse_cli_input(parser: argparse.ArgumentParser) -> dict:
    # Input
    parser.add_argument('-i', '--input', action="extend", nargs="+", default=[], help="The path to the directory with all music files to be read")
    parser.add_argument('-s', '--spotify', action="extend", nargs="+", default=[], help="The URL/URI or ID of a Spotify playlist to search for songs, requires client_id and client_secret")
    parser.add_argument('-it', '--inputTextfile', action="extend", nargs="+", default=[], help="The paths to textfile which contain songs to search for; will enable findAll")

    parser.add_argument('-fa', '--findAll', action="store_true", help="Set to search for ALL songs matching the inputs. Otherwise the parser will try to find exactly one song per search entry")

    # Output
    parser.add_argument("-o", "--output", action="store", default="songs", help="The output directory where all songs and their text files should be saved")

    # Spotify OAuth
    parser.add_argument("-sid", "--spotifyClientId", action="store", help="The Client ID to be used for accessing Spotifies Web API")
    parser.add_argument("-ssc", "--spotifyClientSecret", action="store", help="The Client Secret to be used for accessing Spotifies Web API")

    # usdb.animux Database authentication
    parser.add_argument("-u", "--user", action="store", help="The user to use on http://usdb.animux.de/, required")
    parser.add_argument("-p", "--password", action="store", help="The password for the user, required")

    args = parser.parse_args()

    user_args = {}

    user_args["input_path"] = args.input
    user_args["spotify_input"] = args.spotify
    user_args["inputTextfile"] = args.inputTextfile

    user_args["findAll"] = args.findAll
    if user_args["inputTextfile"]: user_args["findAll"] = True

    input_ways = [user_args["input_path"], user_args["spotify_input"], user_args["inputTextfile"]]

    user_args["output_path"] = args.output

    user_args["spotify_id"] = args.spotifyClientId
    user_args["spotify_secret"] = args.spotifyClientSecret

    user_args["user"] = args.user
    user_args["password"] = args.password

    if not any(input_ways): raise_error("At least one input is required. Exiting...")
    if not (user_args["user"] and user_args["password"]): raise_error("Username and password required. Exiting...")
    if (user_args["spotify_input"] and not (user_args["spotify_id"] and user_args["spotify_secret"])): raise_error("Client ID and secret are required if a Spotify playlist is specified")

    if user_args["input_path"] and not all([os.path.isdir(dir)] for dir in user_args["input_path"]): raise_error(f'{user_args["input_path"]} is not a valid directory. Exiting...')
    if user_args["inputTextfile"] and not all([os.path.isfile(file)] for file in user_args["inputTextfile"]): raise_error(f'{user_args["inputTextfile"]} is not a valid file. Exiting...')

    return user_args

    # TODO: create user if needed

# Main function
def main():

    parser = argparse.ArgumentParser(prog="USDX Song Scraper", description="Scrapes your music files, downloads the USDX text files and according YouTube videos")

    user_args = parse_cli_input(parser)

    search_list = []

    for source_directory in user_args["input_path"]:
        # Get songs from SONG_SOURCE_DIRECTORY and clean those songs from unwanted words and characters
        search_list += clean_search_list(parse_songs_from_directory(directory=source_directory, filetypes=SONG_FILE_TYPES))

    for playlist in user_args["spotify_input"]:
        search_list += parse_songs_from_spotify(user_args["spotify_id"], user_args["spotify_secret"], playlist)

    for textfile in user_args["inputTextfile"]:
        search_list += [line.try_separate() for line in parse_songs_from_textfile(path=textfile)]

    search_list = list(set(search_list))

    # Download HTML Database if necessary
    if not os.path.exists(DATABASE_HTML):
        print("Downloading Database HTML...")
        get_html_database(DATABASE_URL, DATABASE_HTML)

    # Check the HTML for matches
    print("Filtering Database for search results...")
    song_list = search_html_database(DATABASE_HTML, search_list, find_all_matching=user_args["findAll"])
    
    # Remove songs which are already in the output directory
    song_list = remove_duplicates(directory=user_args["output_path"],song_list=song_list)

    # Create cookies based on that
    print("Creating cookies...")
    cookie_list = create_cookies(song_list)
    # Create the payload with user data
    print("Creating payload...")
    payload = create_payload(user_args["user"], user_args["password"])
    # Create users download URL
    print("Creating personal download URL...")
    download_url = create_personal_download_url(user_args["user"])

    folder_list = []

    # Run function for each cookie in cookie_list
    for count, cookie in enumerate(cookie_list):
        print(f"[{(count+1):04d}/{len(cookie_list):04d}] Downloading .txt files with cookie = {cookie[:-1]}")
        # Download txt files with cookie
        try:
            folder = download_usdb_txt(payload, cookie, download_url, user_args["output_path"])
            if not folder in folder_list:
                folder_list.append(folder)
            else:
                print(f"[{(count+1):04d}/{len(cookie_list):04d}] This song already exists, skipping...")
                folder_list.append(None)
        except ConnectionError or requests.exceptions.RetryError:
            print(f"[{(count+1):04d}/{len(cookie_list):04d}] Error while downloading .txt files, skipping {cookie[:-1]}...")
            folder_list.append(None)

    # Create Tuple List and delete entries where folder is not set
    song_folder_tuples = [(song, folder) for song, folder in zip(song_list, folder_list) if folder]

    # Download songs
    for count, (song, folder) in enumerate(song_folder_tuples):
        try: 
            print(f'[{(count+1):04d}/{len(song_folder_tuples):04d}] Getting YT URL for song {song[1]}')
            url = get_yt_url(song=song[1], id=song[0])

            print(f'[{(count+1):04d}/{len(song_folder_tuples):04d}] Downloading {song[1]}')
            folder = download_song(song=song[1], folder=folder, songs_directory=user_args["output_path"], url=url)

            print(f'[{(count+1):04d}/{len(song_folder_tuples):04d}] Cleaning up filenames and references in {folder}')
            clean_tags(songs_directory=user_args["output_path"], song_folder=folder)
        except Exception as e:
            print(f"[{(count+1):04d}/{len(song_folder_tuples):04d}] Error while getting stream or downloading, skipping and trying to delete shallow folder...")
            print(f"Detailed Error: {str(e)}")
            if os.path.isdir(os.path.join(user_args["output_path"], folder)):
                shutil.rmtree(os.path.join(user_args["output_path"], folder))

    print("Finished")
    
    return

if __name__ == "__main__":
    main();