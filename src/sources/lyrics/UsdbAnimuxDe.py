import time

import requests, zipfile, io, os, re
from requests.adapters import HTTPAdapter, Retry
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from math import ceil, floor

from .LyricsSourceBase import LyricsSourceBase

class UsdbAnimuxDe(LyricsSourceBase):

    LOGIN_URL = 'https://usdb.animux.de/index.php?&link=login'
    SONG_URL = 'https://usdb.animux.de/index.php?link=detail&id='
    SEARCH_URL = 'https://usdb.animux.de/?link=list'
    ZIP_URL = 'https://usdb.animux.de/index.php?&link=ziparchiv'
    ZIP_SAVE_URL = 'https://usdb.animux.de/index.php?&link=ziparchiv&save=1'
    DOWNLOAD_URL = "https://usdb.animux.de/data/downloads"

    USERNAME = ''
    PASSWORD = ''
    SESSION = None

    def __init__(self, user_args: dict):
        self.USERNAME = user_args['user'] or os.getenv("USDX_USER")
        self.PASSWORD = user_args['password'] or os.getenv("USDX_PASSWORD")

        if not (self.USERNAME and self.PASSWORD): self.raise_error("Username and password required. Exiting...")

        self.SESSION = self._login()

        super().__init__(user_args)

    def _login(self):
        if self.SESSION: return self.SESSION

        session = requests.Session()
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
        session.mount('https://', HTTPAdapter(max_retries=retries))

        login_payload = self._create_login_payload(self.USERNAME, self.PASSWORD)
        response = session.post(self.LOGIN_URL, data=login_payload)

        if "Login or Password invalid, please try again." in response.text:
            raise Exception("Could not authenticate")

        return session
    
    def _execute_search(self, artist_string: str, title_string: str) -> list[list]:
        payload = self._create_search_payload(interpret=artist_string, title=title_string)
        search_string_representation = f"(artist_string: {artist_string}, title_string: {title_string})"

        response = self.SESSION.post(self.SEARCH_URL, data=payload)

        if "There are  0  results on  0 page(s)" in response.text:
            # print(f"Could not find any results for {search_string_representation}")
            return []

        search_soup = BeautifulSoup(response.text, 'html5lib')

        # Check for next pages
        results_strings = [
            r'There\s*are\s*\d+\s*results\s*on\s*\d+\s*page',
            r'Es gibt\s+\d+\s+Resultate auf\s+\d+ Seite\(n\)'
        ]
        # Look for the string in different languages, take the first one found.
        counter = 0
        for regex in results_strings:
            string_regex = re.compile(regex)
            counter_string = search_soup.find(string=string_regex)
            if counter_string is None:
                continue

            counter = int(re.search(r'\d+', counter_string).group(0))
            if counter > 0:
                print(f"Found counter: {counter}")
                break

        no_of_pages = ceil(counter / 100)
        # print(f"No of Pages: {no_of_pages}")

        search_results = []
        for i in range(no_of_pages):
            if i != 0:
                # print(f"Changing pages to : {i*100}")
                payload = self._create_search_payload(interpret=artist_string, title=title_string, start=i * 100)
                response = self.SESSION.post(self.SEARCH_URL, data=payload)

            search_soup = BeautifulSoup(response.text, 'html5lib')

            result_regex = re.compile(r'list_tr1|list_tr2')
            href_regex = re.compile(r'\?link=detail&id=')
            result_tags = search_soup.findAll("tr",
                                              attrs={"class": result_regex, "onmouseover": "this.className='list_hover'"})

            for tag in result_tags:
                a_tag = tag.find("a", recursive=True, href=href_regex)
                id = parse_qs(urlparse(a_tag.get("href")).query)['id'][0]
                title = a_tag.contents[0]
                artist = tag.find("td").contents[0]

                print(f"Found match: {search_string_representation} -> {artist} - {title}")
                search_results.append([id, f"{artist} - {title}"])

        return search_results

    # Download all Textfiles for USDX from http://usdb.animux.de/
    def _download_lyrics(self, cookie: str, download_url: str, directory: str) -> str:

        # Use the websites cookies to trick the site into putting all of the IDs into one download ZIP
        self.SESSION.cookies.set('counter', '1')
        self.SESSION.cookies.set('ziparchiv', cookie)

        # An authorized request.
        r = self.SESSION.get(self.ZIP_URL)
        if not r.ok: raise ConnectionError
        r = self.SESSION.get(self.ZIP_SAVE_URL)
        if not r.ok: raise ConnectionError
        r = self.SESSION.get(download_url)
        if not r.ok: raise ConnectionError

        # Get ZIP and unpack
        z = zipfile.ZipFile(io.BytesIO(r.content))
        filename, _ = os.path.split(z.namelist()[0])
        z.extractall(directory)

        return filename

    def download_all_lyrics(self, song_list: list) -> list[str]:
        cookie_list = self._create_cookies(song_list)
        download_url = self._create_personal_download_url(self.USERNAME)

        folder_list = []

        # Run function for each cookie in cookie_list
        for count, cookie in enumerate(cookie_list):
            print(f"[{(count + 1):04d}/{len(cookie_list):04d}] Downloading .txt files with cookie = {cookie[:-1]}")
            # Download txt files with cookie
            try:
                folder = self._download_lyrics(cookie, download_url, self.OUTPUT_DIRECTORY)
                if not folder in folder_list:
                    folder_list.append(folder)
                else:
                    print(f"[{(count + 1):04d}/{len(cookie_list):04d}] This song already exists, skipping...")
                    folder_list.append(None)
            except ConnectionError or requests.exceptions.RetryError:
                print(
                    f"[{(count + 1):04d}/{len(cookie_list):04d}] Error while downloading .txt files, skipping {cookie[:-1]}...")
                folder_list.append(None)

        return folder_list

    # Create the payload to login on http://usdb.animux.de/ with the user data
    def _create_search_payload(self, interpret: str = "", title: str = "", edition: str = "", language: str = "",
                              genre: str = "", user: str = "", order: str = "", ud: str = "", limit: int = 100,
                              start: int = 0, ) -> dict[str, str | int]:
        return {
            'interpret': interpret,
            'title': title,
            'edition': edition,
            'language': language,
            'genre': genre,
            'user': user,
            'order': order,
            'ud': ud,
            'limit': limit,
            'start': start
        }

    # Create personal download URL for http://usdb.animux.de/
    def _create_personal_download_url(self, user:str) -> str:
        zip_name = f"{user.lower()}-playlist.zip?t={floor(time.time())}"
        return f"{self.DOWNLOAD_URL}/{zip_name}"

    # Create a list of cookies which contain all song IDs
    def _create_cookies(self, song_list: list) -> list:
        cookie_list = []
        i = 0
        for song in song_list:
            cookie_list.append("")
            cookie_part = song[0] + "|"
            cookie_list[i] += cookie_part
            i += 1

        return cookie_list

    # Create the payload to login on http://usdb.animux.de/ with the user data
    def _create_login_payload(self, user:str, password:str) -> dict[str, str]:
        return {
            'user': user,
            'pass': password,
            'login': 'Login'
        }

    def _get_song_url(self, song_id):
        return self.SONG_URL + song_id
    
        # Get all YouTube URLs: Either from the entry at SONG_URL or via YouTube search
    def get_yt_url(self, song_id: str) -> str:

        song_url = self._get_song_url(song_id=song_id)

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
            return ""