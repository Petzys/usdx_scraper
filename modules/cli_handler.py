import argparse
from datetime import datetime
import sys
import threading
import os
import logging

from modules import config

logger = logging.getLogger(__name__);

##########################################
# Output

def raise_error(err_massage:str):
    logger.critical(err_massage)
    sys.exit(1)

def status_print(level, iterator, count:int, content:str):
    logger.log(level, f'({(count+1):04d}/{len(iterator):04d}) {content}')

def logging_config(user_args:dict) -> list:
    # Create formatter
    formatter_file = logging.Formatter('%(asctime)s - %(filename)s:%(lineno)s - %(funcName)s - %(levelname)s - %(message)s');
    formatter_stdout = CustomFormatter()

    # Create console_handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Add console handler to logger
    console_handler.setFormatter(formatter_stdout)
    handlers = [console_handler]

    if user_args["debug"]:
        file_handler = logging.FileHandler(filename=datetime.now().strftime("usdx_scraper_%H_%M_%S_%d_%m_%Y.log"), encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter_file)
        handlers.append(file_handler)

    return handlers

class CustomFormatter(logging.Formatter):

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = '[%(threadName)s]-[%(levelname)s]: %(message)s'

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


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

    parser.add_argument('-d', '--debug', action="store_true", help="Set to save a log file to the current directory. Default name: usdx_scraper_TIMESTAMP.log")

    args = parser.parse_args()

    user_args = {}

    user_args["input_path"] = args.input
    user_args["spotify_input"] = args.spotify
    user_args["inputTextfile"] = args.inputTextfile

    user_args["findAll"] = args.findAll
    if user_args["inputTextfile"]: user_args["findAll"] = True

    user_args["output_path"] = args.output

    user_args["spotify_id"] = args.spotifyClientId
    user_args["spotify_secret"] = args.spotifyClientSecret

    user_args["user"] = args.user
    user_args["password"] = args.password

    user_args["debug"] = args.debug

    return user_args

    # TODO: create user if needed

def validate_user_args(user_args:dict) -> bool:
    input_ways = [user_args["input_path"], user_args["spotify_input"], user_args["inputTextfile"]]

    if not any(input_ways): 
        raise_error("At least one input is required. Exiting...")

    if not ((user_args["user"] and user_args["password"]) or (config.USDB_USERNAME and config.USDB_PASSWORD)): 
        raise_error("Username and password required. Exiting...")
    if user_args["spotify_input"] and not ((user_args["spotify_id"] and user_args["spotify_secret"]) or (config.SPOTIFY_ID and config.SPOTIFY_SECRET)):
        raise_error("Client ID and secret are required if a Spotify playlist is specified")

    if user_args["input_path"] and not all([os.path.isdir(dir)] for dir in user_args["input_path"]): 
        raise_error(f'{user_args["input_path"]} is not a valid directory. Exiting...')
    if user_args["inputTextfile"] and not all([os.path.isfile(file)] for file in user_args["inputTextfile"]): 
        raise_error(f'{user_args["inputTextfile"]} is not a valid file. Exiting...')

    return True