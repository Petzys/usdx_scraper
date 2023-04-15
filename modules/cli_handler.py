import argparse
import sys
import threading
import os

from modules import config

##########################################
# Output

def raise_error(err_massage:str):
    print(err_massage)
    sys.exit(1)

def status_print(iterator, count:int, content:str):
    print(f'[{threading.current_thread().name}]:[{(count+1):04d}/{len(iterator):04d}] {content}')


##########################################
# User Input

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
    if not ((user_args["user"] and user_args["password"]) or (config.USDB_USERNAME and config.USDB_PASSWORD)): 
        raise_error("Username and password required. Exiting...")
    if user_args["spotify_input"] and not ((user_args["spotify_id"] and user_args["spotify_secret"]) or (config.SPOTIFY_ID and config.SPOTIFY_SECRET)):
        raise_error("Client ID and secret are required if a Spotify playlist is specified")

    if user_args["input_path"] and not all([os.path.isdir(dir)] for dir in user_args["input_path"]): raise_error(f'{user_args["input_path"]} is not a valid directory. Exiting...')
    if user_args["inputTextfile"] and not all([os.path.isfile(file)] for file in user_args["inputTextfile"]): raise_error(f'{user_args["inputTextfile"]} is not a valid file. Exiting...')

    return user_args

    # TODO: create user if needed