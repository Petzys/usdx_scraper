# USDX Scraper
## Download your favorite songs for Ultrastar Deluxe

UltraStar-Deluxe: https://github.com/UltraStar-Deluxe/USDX 

Parses songs from:
- Directories with your songs (mp3, wav, m4a)
- public Spotify playlists
- a input file in the format: `Artist - Title` or `Artist` or `Title` 

You can specify multiple inputs at once.

Output defaults to `./songs/`

### Required parameters
- At least one input (Input directory, Spotify Playlist or Input.txt)
- usdb.animux Credentials
- If Spotify is used: Spotify Web API Credentials (Client ID and secret)

### Config file usdx_scraper_config.yaml
The repository contains a template config which will be used to create a valid `usdx_scraper_config.yaml` on the first run. It contains environment variables for the parser to run and also stores the https://usdb.animux.de/ username and password in addition to the spotify client id and secret for later use. 
If the `usdx_scraper_config.yaml` contains the credentials, it is not necessary to put them in the arguments of the command.

You can also change the number of threads here. It runs on 16 threads by default.

### Docker
Also available on Docker Hub: https://hub.docker.com/r/mrpetzi/usdx_scraper

`docker run -v ${PWD}/docker_input:/data -it usdx_scraper ...`

### Dependencies
The scraper heavily relies https://usdb.animux.de/ to work as it is the main database to my knowledge. Feel free to open an issue if you have ideas for more sources.

### Overview
```
usage: USDX Song Scraper [-h] [-i INPUT [INPUT ...]] [-s SPOTIFY [SPOTIFY ...]] [-it INPUTTEXTFILE [INPUTTEXTFILE ...]] [-fa] [-o OUTPUT]
                         [-sid SPOTIFYCLIENTID] [-ssc SPOTIFYCLIENTSECRET] [-u USER] [-p PASSWORD] [-d]

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
  -sid SPOTIFYCLIENTID, --spotifyClientId SPOTIFYCLIENTID
                        The Client ID to be used for accessing Spotifies Web API
  -ssc SPOTIFYCLIENTSECRET, --spotifyClientSecret SPOTIFYCLIENTSECRET
                        The Client Secret to be used for accessing Spotifies Web API
  -u USER, --user USER  The user to use on http://usdb.animux.de/, required
  -p PASSWORD, --password PASSWORD
                        The password for the user, required
  -d, --debug           Set to save a log file to the current directory. Default name: usdx_scraper_TIMESTAMP.log
```
