import threading
import os, sys, argparse, shutil
import copy

from modules import cli_handler, config, song_parser, thread_handler, txt_files_handler, usdb_handler

CONFIG_FILE_PATH = "config.yaml"

# Main function
def main():
    config_dict = config.load_config(config_file_path=CONFIG_FILE_PATH)
    config.global_config(config=config_dict)

    user_parser = argparse.ArgumentParser(prog="USDX Song Scraper", description="Scrapes your music files, downloads the USDX text files and according YouTube videos")

    user_args = cli_handler.parse_cli_input(parser=user_parser)

    config_dict = config.update_config(config_file_path=CONFIG_FILE_PATH, config=config_dict, user_args=user_args)
    config.global_config(config=config_dict)

    search_list = []

    for source_directory in user_args["input_path"]:
        # Get songs from SONG_SOURCE_DIRECTORY and clean those songs from unwanted words and characters
        search_list += song_parser.clean_search_list(song_parser.parse_songs_from_directory(directory=source_directory, filetypes=config.SONG_FILE_TYPES))

    for playlist in user_args["spotify_input"]:
        search_list += song_parser.parse_songs_from_spotify(config.SPOTIFY_ID, config.SPOTIFY_SECRET, playlist)

    for textfile in user_args["inputTextfile"]:
        search_list += [line.try_separate() for line in song_parser.parse_songs_from_textfile(path=textfile)]

    search_list = list(set(search_list))
    print(f"Found {len(search_list)} items!")

    # Check the USDB for matches
    print("Searching for matches...")
    
    # Create the payload with user data
    print("Creating payload...")
    payload = usdb_handler.create_login_payload(config.USDB_USERNAME, config.USDB_PASSWORD)

    song_list = usdb_handler.native_search(login_payload=payload, search_list=search_list, find_all_matching=user_args["findAll"])
    
    # Remove songs which are already in the output directory
    song_list = txt_files_handler.remove_duplicates(directory=user_args["output_path"],song_list=song_list)

    # Create cookies based on that
    print("Creating cookies...")
    cookie_list = usdb_handler.create_cookies(song_list)

    # Create users download URL
    print("Creating personal download URL...")
    download_url = usdb_handler.create_personal_download_url(config.USDB_USERNAME)

    # Thread folder names
    thread_folders = []
    for i in range(config.THREAD_NUMBER):
        thread_folders.append(f"t_{i}")

    sliced_cookie_tuple = thread_handler.split(list=cookie_list, number_spliced_lists=config.THREAD_NUMBER)
    threads = [None] * config.THREAD_NUMBER
    target = [None] * config.THREAD_NUMBER
    for i in range(config.THREAD_NUMBER):
        cloned_user_args = copy.deepcopy(user_args)
        cloned_user_args["output_path"] = os.path.join(cloned_user_args["output_path"], thread_folders[i])
        args = (sliced_cookie_tuple[i], payload, download_url, cloned_user_args, i, target)
        threads[i] = threading.Thread(target=thread_handler.thread_runner_txt, args=args, name=f"THREAD_TXT_{i}")
        threads[i].start()

    for i in range(config.THREAD_NUMBER):
        threads[i].join()

    folder_list = [item for sublist in target for item in sublist]

    # Create Tuple List and delete entries where folder is not set
    song_folder_tuples = [(song, folder) for song, folder in zip(song_list, folder_list) if folder]

    # Download songs
    sliced_song_folder_tuples = thread_handler.split(list=song_folder_tuples, number_spliced_lists=config.THREAD_NUMBER)
    for i in range(config.THREAD_NUMBER):
        cloned_user_args = copy.deepcopy(user_args)
        cloned_user_args["output_path"] = os.path.join(cloned_user_args["output_path"], thread_folders[i])
        args = (sliced_song_folder_tuples[i], cloned_user_args)
        threads[i] = threading.Thread(target=thread_handler.thread_runner_download, args=args, name=f"THREAD_DOWNLOAD_{i}")
        threads[i].start()

    for i in range(config.THREAD_NUMBER):
        threads[i].join()

    # Moving files from thread folders
    for folder in thread_folders:
        full_thread_folder_path = os.path.join(user_args["output_path"], folder)
        if os.path.isdir(full_thread_folder_path):
            for song in os.listdir(full_thread_folder_path):
                full_song_path = os.path.join(full_thread_folder_path, song)
                target_path = os.path.join(user_args["output_path"], song)
                if os.path.isdir(full_song_path) and not os.path.exists(target_path):
                    shutil.move(full_song_path, target_path)
        shutil.rmtree(full_thread_folder_path)

    print("Finished")
    
    return

if __name__ == "__main__":
    main();
    sys.exit(0)