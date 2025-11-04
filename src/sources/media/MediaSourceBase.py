from abc import ABCMeta, abstractmethod

class MediaSourceBase(metaclass=ABCMeta):
    def __init__(self, user_args):
        pass

    @abstractmethod
    def download_audio(self, song: str, song_folder_path: str):
        pass

    @abstractmethod
    def download_video(self, song:str, song_folder_path:str):
        pass
