import os, re
import yt_dlp
from requests.adapters import HTTPAdapter, Retry
from youtubesearchpython import VideosSearch

from src.sources.lyrics.LyricsSourceBase import LyricsSourceBase
from src.sources.lyrics.UsdbAnimuxDe import UsdbAnimuxDe
from src.sources.media.MediaSourceBase import MediaSourceBase


class Youtube(MediaSourceBase):

    maximum_video_resolution = "480"
    lyrics_source: LyricsSourceBase

    def __init__(self, user_args, lyrics_source: LyricsSourceBase):
        self.maximum_video_resolution = user_args["maximum_video_resolution"] or os.getenv("MAX_VIDEO_RESOLUTION") or self.maximum_video_resolution
        self.lyrics_source = lyrics_source
        super().__init__(user_args)

    def download_audio(self, song:list, song_folder_path:str) -> str:
        yt_opts_mp3 = {
            'format': 'bestaudio',
            'outtmpl': f'{song_folder_path}/{song[1]}',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }],
            'quiet': True,
            'nooverwrites': True,
            'no_warnings': True,
        }
        if isinstance(self.lyrics_source, UsdbAnimuxDe):
            url = self.lyrics_source.get_yt_url(song_id=song[0])
        else:
            url = self.search_yt(song[1])

        self.download_song(url=url, yt_options=yt_opts_mp3)

        return song[1]

    def download_video(self, song:list, song_folder_path:str) -> str:
        yt_opts_mp4 = {
            'format': f"bestvideo[height<={self.maximum_video_resolution}][ext=m4a]+bestaudio[ext=m4a]/best[height<={self.maximum_video_resolution}][ext=mp4]/best",
            'outtmpl': f'{song_folder_path}/{song[1]}.mp4',
            'quiet': True,
            'nooverwrites': True,
            'no_warnings': True,
        }
        if isinstance(self.lyrics_source, UsdbAnimuxDe):
            url = self.lyrics_source.get_yt_url(song_id=song[0])
        else:
            url = self.search_yt(song[1])

        self.download_song(url=url, yt_options=yt_opts_mp4)

        return song[1]

    @staticmethod
    def download_song(url, yt_options) -> None:
        with yt_dlp.YoutubeDL(yt_options) as ydl:
            ydl.download([url])

    # Search for videos on YT and add links to song_list
    @staticmethod
    def search_yt(song: str) -> str:
        search_key = re.sub(
            r"\s*\([Dd][Uu][Ee][Tt]\)\s*|\s*\[[Dd][Uu][Ee][Tt]\]\s*|\s*\{[Dd][Uu][Ee][Tt]\}\s*|\s*[Dd][Uu][Ee][Tt]\s*",
            "", song)
        print(f"Searching for: {search_key} Music Video")
        videos_search = VideosSearch(f'{search_key} Music Video', limit=1)
        return videos_search.result()["result"][0]["link"]