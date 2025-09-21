import requests, os, sys, argparse, shutil
import yt_dlp
import copy
from dotenv import load_dotenv

from src.sources.SongSearchItem import SongSearchItem
from src.sources.lyrics.UsdbAnimuxDe import UsdbAnimuxDe
from src.sources.songs.Directory import Directory
from src.sources.songs.File import File
from src.sources.songs.Spotify import Spotify


def raise_error(err_massage:str):
    print(err_massage)
    sys.exit(1)



def add_switched_search_items(search_list:list[SongSearchItem]) -> list[SongSearchItem]:
    new_list = copy.deepcopy(search_list)
    for item in search_list:
        #print(f"Appending switched item {SongSearchItem(item.artist_tag_tuple, item.name_tag_tuple)}")
        new_list.append(SongSearchItem(item.artist_tag_tuple, item.name_tag_tuple))

    return new_list

# Validate all the flags in a txt file and overwrite all that are different to the parameter
def validate_txt_tags(file_path:str, tags:dict[str, str], encoding: str):
    # First read all the lines and get current tags
    current_tags = {}
    with open(file_path, 'r', encoding=encoding) as file:
        lines = file.readlines()
        # Create dict with tag as key and value as value
        current_tags = {line.split(":")[0][1:]:line.split(":")[1] for line in lines if line.startswith("#")}
        content = lines[len(current_tags):]

    # Merge both dicts, tags is dominant and overwrites current_tags if keys match
    new_tags = current_tags | tags

    # Write all new tags to the file and append rest of file
    with open(file_path, 'w',  encoding=encoding) as file:
        file.writelines([f"#{key}:{value}" for key,value in new_tags.items()])
        file.writelines(content)

# Rename all tags in the txt files to match the files in the directory
def clean_tags(songs_directory:str, song_folder:str):
    tags = {}
    txt = ""
    files = os.listdir(os.path.join(songs_directory, song_folder))
    for file in files:
        # Set the tags to set with validate_txt_tags()
        filetype = os.path.splitext(file)[-1]
        match filetype:
            case (".mp3" | ".mp4"):
                tags["MP3"] = f"{file}\n"
                tags["VIDEO"] = f"{file}\n"
            case ".jpg":
                tags["COVER"] = f"{file}\n"
            case ".txt":
                txt = file
    try:
        validate_txt_tags(os.path.join(songs_directory, song_folder, txt), tags, "cp1252")
    except:
        # Some song files require using the cp1252-Encoding, while other files require using the utf-8-Encoding instead.
        validate_txt_tags(os.path.join(songs_directory, song_folder, txt), tags, "utf-8")

def rename_song_folder_and_contents(song:str, folder:str, songs_directory:str) -> str:
    song_directory_contents = os.listdir(songs_directory)
    song_folder = os.path.join(songs_directory, song)

    # Rename folder to match the song name
    if song in song_directory_contents:
        #print(f"Tried to rename but folder already exists! Keeping old names... {desired_path}")
        song_folder = os.path.join(songs_directory, folder)
        song = folder
    elif folder in song_directory_contents:
        os.rename(os.path.join(songs_directory, folder), song_folder)
    else:
        print(f"Could not find directory {os.path.join(songs_directory, folder)}")
        raise FileNotFoundError

    # Rename all files in the folder to match the song name
    for file in os.listdir(song_folder):
        file_ending = os.path.splitext(file)[-1]
        if os.path.isfile(os.path.join(song_folder, file)):
            os.rename(os.path.join(song_folder, file), os.path.join(song_folder, f"{song}{file_ending}"))
        else:
            print(f"Could not find file {os.path.join(song_folder, file)}")
            raise FileNotFoundError

    return song_folder

def download_song(song:str, song_folder_path:str, url:str, file_media_type: str, max_video_resolution: str) -> str:
    yt_opts_mp4 = {
        'format': f"bestvideo[height<={max_video_resolution}][ext=m4a]+bestaudio[ext=m4a]/best[height<={max_video_resolution}][ext=mp4]/best",
        'outtmpl': f'{song_folder_path}/{song}.mp4',
        'quiet': True,
        'nooverwrites': True,
    }

    yt_opts_mp3 = {
        'format': 'bestaudio',
        'outtmpl': f'{song_folder_path}/{song}',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
        'quiet': True,
        'nooverwrites': True,
    }

    yt_opts = yt_opts_mp3 if file_media_type == "MP3" else yt_opts_mp4
    with yt_dlp.YoutubeDL(yt_opts) as ydl:
        ydl.download([url])

    return song

def remove_duplicates(directory:str, song_list:list[list]) -> list[list]:
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
    parser.add_argument("-o", "--output", action="store", default="", help="The output directory where all songs and their text files should be saved")
    parser.add_argument("-ft", "--filetype", action="store", default="MP3", help="The file type to be used for the downloaded songs. Either MP3 or MP4. Default is MP3")
    parser.add_argument("-mvr", "--maxVidRes", action="store", default="480", help="Maximum video resolution to be used for the downloaded songs. Default is 480p. Only used if filetype is MP4")

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

    user_args["output_path"] = args.output or os.getenv("OUTPUT_DIRECTORY")
    user_args["media_filetype"] = args.filetype
    user_args["maximum_video_resolution"] = args.maxVidRes

    user_args["spotify_id"] = args.spotifyClientId
    user_args["spotify_secret"] = args.spotifyClientSecret

    user_args["user"] = args.user or os.getenv("USDX_USER")
    user_args["password"] = args.password or os.getenv("USDX_PASSWORD")

    if not any(input_ways): raise_error("At least one input is required. Exiting...")

    return user_args

    # TODO: create user if needed

# Main function
def main():
    parser = argparse.ArgumentParser(prog="USDX Song Scraper", description="Scrapes your music files, downloads the USDX text files and according YouTube videos")

    load_dotenv()
    user_args = parse_cli_input(parser)

    search_list = []
    
    lyric_sources = {
        UsdbAnimuxDe.__class__:UsdbAnimuxDe(user_args),
    }

    song_sources = {
        Spotify.__class__:Spotify(user_args),
        Directory.__class__:Directory(user_args),
        File.__class__:File(user_args),
    }
    
    for source in song_sources:
        search_list += song_sources[source].get_song_list()

    search_list = list(set(search_list))

    # Right now we only have one lyrics source, so we can just use that one.
    #todo Later we should add https://usdb.hehoe.de/ and the LyricSources mentioned on there.
    lyrics_source = lyric_sources[UsdbAnimuxDe.__class__]

    full_search_list = add_switched_search_items(search_list=search_list)
    song_list = lyrics_source.native_search(search_list=full_search_list, find_all_matching=user_args["findAll"])

    # Remove songs which are already in the output directory
    #todo shouldn't we remove existing songs *before* the search?
    song_list = remove_duplicates(directory=user_args["output_path"], song_list=song_list)

    # Create cookies based on that
    print("Downloading lyrics")

    folder_list = lyrics_source.download_all_lyrics(song_list=song_list)

    # Create Tuple List and delete entries where folder is not set
    song_folder_tuples = [(song, folder) for song, folder in zip(song_list, folder_list) if folder]

    # Download songs
    for count, (song, folder) in enumerate(song_folder_tuples):
        try:
            print(f'[{(count+1):04d}/{len(song_folder_tuples):04d}] Getting YT URL for song {song[1]}')
            url = lyrics_source.get_yt_url(song=song[1], id=song[0])

            print(f'[{(count+1):04d}/{len(song_folder_tuples):04d}] Downloading {song[1]}')
            song_folder_path = rename_song_folder_and_contents(song=song[1], folder=folder, songs_directory=user_args["output_path"])
            folder = download_song(song=song[1], song_folder_path=song_folder_path, url=url, file_media_type=user_args["media_filetype"], max_video_resolution=user_args["maximum_video_resolution"])

            print(f'[{(count+1):04d}/{len(song_folder_tuples):04d}] Cleaning up filenames and references in {folder}')
            clean_tags(songs_directory=user_args["output_path"], song_folder=folder)
        except Exception as e:
            print(f"[{(count+1):04d}/{len(song_folder_tuples):04d}] Error while getting stream or downloading, skipping and trying to delete shallow folder...")
            print(f"Detailed Error: {str(e)}")
            if folder in os.listdir(user_args["output_path"]):
                shutil.rmtree(os.path.join(user_args["output_path"], folder))

    print("Finished")

    return

if __name__ == "__main__":
    main()
    sys.exit(0)