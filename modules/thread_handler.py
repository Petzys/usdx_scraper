import os
import shutil
import requests
import logging

from modules import cli_handler, usdb_handler, youtube_handler, txt_files_handler

logger = logging.getLogger(__name__)

def thread_runner_txt(cookie_list:list, payload:str, download_url:str, user_args:dict, index:int, target:list):
    folder_list = []

    # Run function for each cookie in cookie_list
    for count, cookie in enumerate(cookie_list):
        cli_handler.status_print(level=logging.DEBUG, iterator=cookie_list, count=count, content=f'Downloading .txt files with cookie = {cookie[:-1]}')
        
        # Download txt files with cookie
        try:
            folder = usdb_handler.download_usdb_txt(payload, cookie, download_url, user_args["output_path"])
            if not folder in folder_list:
                folder_list.append(folder)
            else:
                cli_handler.status_print(level=logging.DEBUG, iterator=cookie_list, count=count, content=f'This song already exists, skipping...')
                folder_list.append(None)
        except ConnectionError or requests.exceptions.RetryError:
            cli_handler.status_print(level=logging.WARNING, iterator=cookie_list, count=count, content=f'Error while downloading .txt files, skipping {cookie[:-1]}...')
            folder_list.append(None)

    target[index] = folder_list

def thread_runner_download(song_folder_tuples:tuple, user_args:dict): 
    # Download songs
    for count, (song, folder) in enumerate(song_folder_tuples):
        try: 
            cli_handler.status_print(level=logging.DEBUG, iterator=song_folder_tuples, count=count, content=f'Getting YT URL for song {song[1]}')
            url = youtube_handler.get_yt_url(song=song[1], id=song[0])

            cli_handler.status_print(level=logging.DEBUG, iterator=song_folder_tuples, count=count, content=f'Downloading {song[1]}')
            folder = youtube_handler.download_song(song=song[1], folder=folder, songs_directory=user_args["output_path"], url=url)

            cli_handler.status_print(level=logging.DEBUG, iterator=song_folder_tuples, count=count, content=f'Cleaning up filenames and references in {folder}')
            txt_files_handler.clean_tags(songs_directory=user_args["output_path"], song_folder=folder)
        
        except Exception as e:
            cli_handler.status_print(level=logging.WARNING, iterator=song_folder_tuples, count=count, content=f'Error while getting stream or downloading, skipping and deleting shallow folder...')
            
            logger.error(f"Detailed Error: {str(e)}")
            if folder in os.listdir(user_args["output_path"]):
                shutil.rmtree(os.path.join(user_args["output_path"], folder))
            
    return

def split(list, number_spliced_lists) -> list:
    k, m = divmod(len(list), number_spliced_lists)
    return [list[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(number_spliced_lists)]