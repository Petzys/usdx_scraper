import copy
import io
from math import ceil
import os
import re
from urllib.parse import parse_qs, urlparse
import zipfile
from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter, Retry

from modules import config, song_parser

##### Login #####
# Create the payload to login on http://usdb.animux.de/ with the user data
def create_login_payload(user:str, password:str) -> str:
    return {
        'user': user,
        'pass': password,
        'login': 'Login'
    }

##### Search #####
# Create the payload to login on http://usdb.animux.de/ with the user data
def create_search_payload(interpret:str="", title:str="", edition:str="", language:str="", genre:str="", user:str="", order:str="", ud:str="", limit:int=100, start:int=0,) -> str:
    return {
        'interpret':interpret,
        'title':title,
        'edition':edition,
        'language':language,
        'genre':genre,
        'user':user,
        'order':order,
        'ud':ud,
        'limit':limit, 
        'start':start
    }

def add_switched_search_items(search_list:list[song_parser.SongSearchItem]) -> list[song_parser.SongSearchItem]:
    new_list = copy.deepcopy(search_list)
    for item in search_list:
        #print(f"Appending switched item {SongSearchItem(item.artist_tag_tuple, item.name_tag_tuple)}")
        new_list.append(song_parser.SongSearchItem(item.artist_tag_tuple, item.name_tag_tuple))

    return new_list

def native_search(login_payload:dict, search_list:list[song_parser.SongSearchItem], find_all_matching:bool) -> list[list]:
    search_list = add_switched_search_items(search_list=search_list)

    song_list = [];

    with requests.Session() as session:

        retries = Retry(total=5, backoff_factor=1, status_forcelist=[ 502, 503, 504 ])
        session.mount('https://', HTTPAdapter(max_retries=retries))

        response = session.post(config.LOGIN_URL, data=login_payload)

        if "Login or Password invalid, please try again." in response.text:
            raise Exception("Could not authenticate");

        for count, search_item in enumerate(search_list):
            artist_string = " ".join(search_item.artist_tag_tuple)
            title_string = " ".join(search_item.name_tag_tuple)
            payload = create_search_payload(interpret=artist_string, title=title_string)

            response = session.post(config.SEARCH_URL, data=payload)

            if "There are  0  results on  0 page(s)" in response.text:
                continue

            search_soup = BeautifulSoup(response.text, 'html5lib')

            # Check for next pages
            string_regex = re.compile(r'There\s*are\s*\d{0,9999}\s*results\s*on\s*\d{0,9999}\s*page')
            counter_string = search_soup.find(string=string_regex)
            #print(f"Found counter String: {counter_string}")
            
            counter = int(re.search(r'\d+', counter_string).group(0))
            #print(f"Found counter: {counter}")
            
            no_of_pages = ceil(counter/100)
            #print(f"No of Pages: {no_of_pages}")

            for i in range(no_of_pages):
                if i != 0:
                    #print(f"Changing pages to : {i*100}")
                    payload = create_search_payload(interpret=artist_string, title=title_string, start=i*100)
                    response = session.post(config.SEARCH_URL, data=payload)

                search_soup = BeautifulSoup(response.text, 'html5lib')

                result_regex = re.compile(r'list_tr1|list_tr2')
                href_regex = re.compile(r'\?link=detail&id=')
                result_tags = search_soup.findAll("tr", attrs={"class":result_regex, "onmouseover":"this.className='list_hover'"})

                for tag in result_tags:
                    a_tag = tag.find("a", recursive=True, href=href_regex)
                    id = parse_qs(urlparse(a_tag.get("href")).query)['id'][0]
                    title = a_tag.contents[0]
                    artist = tag.find("td").contents[0]

                    print(f"Found match: {search_item} -> {artist} - {title}")
                    song_list.append([id, f"{artist} - {title}"])

            if not find_all_matching: search_list.pop(count)

    return song_list


##### TXT Download #####
# Create personal download URL for http://usdb.animux.de/
def create_personal_download_url(user:str) -> str:
    return f"{config.DOWNLOAD_URL}/{user}'s%20Playlist.zip"

# Create a list of cookies which contain all song IDs
def create_cookies(song_list:list) -> list:
    cookie_list = []
    i = 0
    for song in song_list:
        cookie_list.append("")
        cookie_part = song[0] + "|"
        cookie_list[i] += cookie_part
        i += 1

    return cookie_list

# Download all Textfiles for USDX from http://usdb.animux.de/
def download_usdb_txt(payload:str, cookie:str, download_url:str, directory:str) -> str:
    with requests.Session() as session:

        retries = Retry(total=5, backoff_factor=1, status_forcelist=[ 502, 503, 504 ])
        session.mount('https://', HTTPAdapter(max_retries=retries))

        response = session.post(config.LOGIN_URL, data=payload)

        if "Login or Password invalid, please try again." in response.text:
            raise Exception("Could not authenticate");

        # Use the websites cookies to trick the site into putting all of the IDs into one download ZIP
        session.cookies.set('counter', '1');
        session.cookies.set('ziparchiv', cookie);

        # An authorized request.
        r = session.get(config.ZIP_URL)
        if not r.ok: raise ConnectionError
        r = session.get(config.ZIP_SAVE_URL)
        if not r.ok: raise ConnectionError
        r = session.get(download_url)
        if not r.ok: raise ConnectionError
        
        # Get ZIP and unpack
        z = zipfile.ZipFile(io.BytesIO(r.content))
        filename, _ = os.path.split(z.namelist()[0])
        z.extractall(directory)

    return filename