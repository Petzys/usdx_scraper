# Get all YouTube URLs: Either from the entry at SONG_URL or via YouTube search
import os
import re
from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter, Retry
from youtubesearchpython import VideosSearch
from pytube import YouTube

from modules import config

def get_yt_url(song:str, id:str) -> str:
    with requests.Session() as session:
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[ 502, 503, 504 ])
        session.mount('https://', HTTPAdapter(max_retries=retries))

        # Try to find if there a link to a YT video on the songs https://usdb.animux.de/ page
        r = session.get(config.SONG_URL+id)
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

    if song in os.listdir(songs_directory):
        #print(f"Tried to rename but folder already exists! Keeping old names... {desired_path}")
        desired_path = os.path.join(songs_directory, folder)
        song = folder
    elif folder in os.listdir(songs_directory):
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