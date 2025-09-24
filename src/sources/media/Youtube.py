import requests, os, re
import yt_dlp
from requests.adapters import HTTPAdapter, Retry
from bs4 import BeautifulSoup
from youtubesearchpython import VideosSearch

from src.sources.lyrics.LyricsSourceBase import LyricsSourceBase
from src.sources.media.MediaSourceBase import MediaSourceBase


class Youtube(MediaSourceBase):

    maximum_video_resolution = "1080"

    def __init__(self, user_args):
        self.maximum_video_resolution = user_args["maximum_video_resolution"] or os.getenv("MAX_VIDEO_RESOLUTION") or self.maximum_video_resolution
        super().__init__(user_args)

    # Get all YouTube URLs: Either from the entry at SONG_URL or via YouTube search
    @staticmethod
    def get_yt_url(song: str, song_id: str, lyrics_source: LyricsSourceBase) -> str:

        song_url = lyrics_source.get_song_url(song_id=song_id)

        with requests.Session() as session:
            retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
            session.mount('https://', HTTPAdapter(max_retries=retries))

            # Try to find if there is a link to a YT video on the songs http://usdb.animux.de/ page
            r = session.get(song_url)
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
            search_key = re.sub(
                r"\s*\([Dd][Uu][Ee][Tt]\)\s*|\s*\[[Dd][Uu][Ee][Tt]\]\s*|\s*\{[Dd][Uu][Ee][Tt]\}\s*|\s*[Dd][Uu][Ee][Tt]\s*",
                "", song)
            print(f"Searching for: {search_key} Music Video")
            videos_search = VideosSearch(f'{search_key} Music Video', limit=1)
            return videos_search.result()["result"][0]["link"]


    def download_mp3(self, song:list, song_folder_path:str, lyrics_source: LyricsSourceBase) -> str:
        yt_opts_mp3 = {
            'format': 'bestaudio',
            'outtmpl': f'{song_folder_path}/{song[1]}',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }],
            'quiet': True,
            'nooverwrites': True,
        }
        url = self.get_yt_url(song=song[1], song_id=song[0], lyrics_source=lyrics_source)

        self.download_song(url=url, yt_options=yt_opts_mp3)

        return song[1]

    def download_mp4(self, song:list, song_folder_path:str, lyrics_source: LyricsSourceBase) -> str:
        yt_opts_mp4 = {
            'format': f"bestvideo[height<={self.maximum_video_resolution}][ext=m4a]+bestaudio[ext=m4a]/best[height<={self.maximum_video_resolution}][ext=mp4]/best",
            'outtmpl': f'{song_folder_path}/{song[1]}.mp4',
            'quiet': True,
            'nooverwrites': True,
        }
        url = self.get_yt_url(song=song[1], song_id=song[0],lyrics_source=lyrics_source)

        self.download_song(url=url, yt_options=yt_opts_mp4)

        return song[1]

    @staticmethod
    def download_song(url, yt_options) -> None:
        with yt_dlp.YoutubeDL(yt_options) as ydl:
            ydl.download([url])