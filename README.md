# USDX Scraper
## Download your favorite songs for Ultrastar Deluxe

UltraStar-Deluxe: https://github.com/UltraStar-Deluxe/USDX 

Parses songs from:
- Directories with your songs (mp3, wav, m4a)
- public Spotify Playlists
- a input file in the format: `Artist - Title`

You can specify multiple inputs at once.

Output defaults to `./songs/`

Required parameters:
- At least one input (Input directory, Spotify Playlist or Input.txt)
- usdb.animux Credentials
- If Spotify is used: Spotify Web API Credentials (Client ID and secret)

Also available on Docker Hub: https://hub.docker.com/r/mrpetzi/usdx_scraper

The scraper heavily relies on https://usdb.hehoe.de/ and http://usdb.animux.de/ to work. Might optimize this in the future.

## ENV File
You can copy the `.env.example` file to `.env` and fill in the required parameters:
- OUTPUT_DIRECTORY
- INPUT_FILE_PATH
- INPUT_DIRECTORY_PATH
- USDX_USER
- USDX_PASSWORD
- SPOTIPY_CLIENT_ID
- SPOTIPY_CLIENT_SECRET
- SPOTIPY_PLAYLIST_ID  
- MAX_VIDEO_RESOLUTION=480
- MEDIA_FILETYPE=MP3


```
usage: USDX Song Scraper [-h] [-i INPUT [INPUT ...]] [-s SPOTIFY [SPOTIFY ...]] [-it INPUTTEXTFILE [INPUTTEXTFILE ...]] [-fa] [-o OUTPUT] [-sid SPOTIFYCLIENTID] [-ssc SPOTIFYCLIENTSECRET] [-u USER] [-p PASSWORD]

Scrapes your music files, downloads the USDX text files and according YouTube videos

options:
  -h, --help            show this help message and exit
  -i INPUT [INPUT ...], --input INPUT [INPUT ...]
                        The path to the directory with all music files to be read
  -s SPOTIFY [SPOTIFY ...], --spotify SPOTIFY [SPOTIFY ...]
                        The URL/URI or ID of a Spotify playlist to search for songs, requires client_id and client_secret
  -it INPUTTEXTFILE [INPUTTEXTFILE ...], --inputTextfile INPUTTEXTFILE [INPUTTEXTFILE ...]
                        The paths to textfile which contain songs to search for; will enable findAll
  -fa, --findAll        Set to search for ALL songs matching the inputs. Otherwise the parser will try to find exactly one song per search entry
  -o OUTPUT, --output OUTPUT
                        The output directory where all songs and their text files should be saved
  -ft FILETYPE, --filetype FILETYPE
                        The file type to be used for the downloaded songs. Either MP3 or MP4. Default is MP3
  -mvr MAXVIDRES, --maxVidRes MAXVIDRES
                        Maximum video resolution to be used for the downloaded songs. Default is 480p. Only used if filetype is MP4
  -sid SPOTIFYCLIENTID, --spotifyClientId SPOTIFYCLIENTID
                        The Client ID to be used for accessing Spotifies Web API
  -ssc SPOTIFYCLIENTSECRET, --spotifyClientSecret SPOTIFYCLIENTSECRET
                        The Client Secret to be used for accessing Spotifies Web API
  -u USER, --user USER  The user to use on http://usdb.animux.de/, required
  -p PASSWORD, --password PASSWORD
                        The password for the user, required
```
