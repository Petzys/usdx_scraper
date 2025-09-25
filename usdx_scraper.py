import os, sys, argparse
import copy
from dotenv import load_dotenv

from src.sources.ColorPrint import ColorPrint
from src.sources.Filesystem import Filesystem
from src.sources.SongSearchItem import SongSearchItem
from src.sources.lyrics.UsdbAnimuxDe import UsdbAnimuxDe
from src.sources.media.Youtube import Youtube
from src.sources.songs.Directory import Directory
from src.sources.songs.File import File
from src.sources.songs.Spotify import Spotify


def raise_error(err_massage:str):
    ColorPrint.print(ColorPrint.FAIL, err_massage)
    sys.exit(1)

# Expand the list by switching the artist and title tags.
def add_switched_search_items(search_list:list[SongSearchItem]) -> list[SongSearchItem]:
    new_list = copy.deepcopy(search_list)
    for item in search_list:
        #print(f"Appending switched item {SongSearchItem(item.artist_tag_tuple, item.name_tag_tuple)}")
        new_list.append(SongSearchItem(item.artist_tag_tuple, item.name_tag_tuple))

    return new_list

# Parse the CLI input
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

    if args.output and not os.path.isdir(args.output):
        raise_error(f"Output directory {args.output} does not exist.")

    if args.maxVidRes and args.maxVidRes not in ("360", "480", "720", "1080"):
        raise_error("Invalid maximum video resolution. Valid options are 360, 480, 720 and 1080.")

    if args.filetype and args.filetype not in ("MP3", "MP4"):
        raise_error("Invalid filetype. Valid options are MP3 and MP4.")

    user_args = {}

    user_args["input_path"] = args.input
    user_args["spotify_input"] = args.spotify
    user_args["inputTextfile"] = args.inputTextfile

    user_args["findAll"] = args.findAll
    if user_args["inputTextfile"]: user_args["findAll"] = True

    user_args["output_path"] = args.output or os.getenv("OUTPUT_DIRECTORY") or "./output"
    user_args["media_filetype"] = args.filetype or os.getenv("MEDIA_FILETYPE") or "MP3"
    user_args["maximum_video_resolution"] = args.maxVidRes

    user_args["spotify_id"] = args.spotifyClientId
    user_args["spotify_secret"] = args.spotifyClientSecret

    user_args["user"] = args.user or os.getenv("USDX_USER")
    user_args["password"] = args.password or os.getenv("USDX_PASSWORD")

    return user_args

    # TODO: create user if needed

# Main function
def main():
    parser = argparse.ArgumentParser(prog="USDX Song Scraper", description="Scrapes your music files, downloads the USDX text files and according YouTube videos")

    # Load environment variables from .env file
    load_dotenv()
    user_args = parse_cli_input(parser)

    Filesystem.ensure_output_directory(output_path=user_args["output_path"])

    # Create sources
    lyric_sources = {
        UsdbAnimuxDe.__class__:UsdbAnimuxDe(user_args),
    }

    song_sources = {
        Spotify.__class__:Spotify(user_args),
        Directory.__class__:Directory(user_args),
        File.__class__:File(user_args),
    }

    media_sources = {
        Youtube.__class__:Youtube(user_args),
    }

    # Go through all the sources and get a list of all songs
    search_list = []
    for source in song_sources:
        search_list += song_sources[source].get_song_list()

    # Remove duplicate elements in the list.
    # Happens if the songs are in multiple sources.
    search_list = list(set(search_list))

    # Right now we only have one lyrics source, so we can just use that one.
    #todo Later we should add https://usdb.hehoe.de/ and the LyricSources mentioned on there.
    lyrics_source = next(iter(lyric_sources.values()))

    full_search_list = add_switched_search_items(search_list=search_list)
    song_list = lyrics_source.native_search(search_list=full_search_list, find_all_matching=user_args["findAll"])

    # Remove songs which are already in the output directory
    #todo shouldn't we remove existing songs *before* the search?
    song_list = Filesystem.remove_duplicates(directory=user_args["output_path"], song_list=song_list)

    # Create cookies based on that
    print("Downloading lyrics")

    folder_list = lyrics_source.download_all_lyrics(song_list=song_list)

    # Create Tuple List and delete entries where folder is not set
    song_folder_tuples = [(song, folder) for song, folder in zip(song_list, folder_list) if folder]

    # Right now we only have one media source, so we can just use that one.
    #todo think about adding more sources. YouTube can't be the only source.
    media_source = media_sources[Youtube.__class__]

    # Download songs

    # Decide on which download method to be used.
    downloader = media_source.download_mp3
    if user_args["media_filetype"] == "MP4":
        downloader = media_source.download_mp4

    for count, (song, folder) in enumerate(song_folder_tuples):
        try:
            print(f'[{(count+1):04d}/{len(song_folder_tuples):04d}] Downloading {song[1]}')
            song_folder_path = Filesystem.rename_song_folder_and_contents(
                song=song[1],
                folder=folder,
                songs_directory=user_args["output_path"]
            )

            folder = downloader(song=song, song_folder_path=song_folder_path, lyrics_source=lyrics_source)

            print(f'[{(count+1):04d}/{len(song_folder_tuples):04d}] Cleaning up filenames and references in {folder}')
            Filesystem.clean_tags(songs_directory=user_args["output_path"], song_folder=folder)
        except Exception as e:
            ColorPrint.print(ColorPrint.FAIL, f"[{(count+1):04d}/{len(song_folder_tuples):04d}] Error while getting stream or downloading. Skipping...")
            ColorPrint.print(ColorPrint.FAIL, f"Detailed Error: {str(e)}")


    print("Finished")

    return

if __name__ == "__main__":
    main()
    sys.exit(0)