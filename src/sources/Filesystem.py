import os
class Filesystem:

    @staticmethod
    def ensure_output_directory(output_path: str):
        if not os.path.isdir(output_path):
            os.makedirs(output_path)

    @staticmethod
    def rename_song_folder_and_contents(song: str, folder: str, songs_directory: str) -> str:
        song_directory_contents = os.listdir(songs_directory)
        song_folder = os.path.join(songs_directory, song)

        # Rename folder to match the song name
        if song in song_directory_contents:
            # print(f"Tried to rename but folder already exists! Keeping old names... {desired_path}")
            song_folder = os.path.join(songs_directory, folder)
            song = folder
        elif folder in song_directory_contents:
            os.rename(os.path.join(songs_directory, folder), song_folder)
        else:
            print(f"Could not find directory {os.path.join(songs_directory, folder)}")
            raise FileNotFoundError

        # Rename all files in the folder to match the song name
        for file in os.listdir(song_folder):
            file_ending = os.path.splitext(file)[-1]
            if os.path.isfile(os.path.join(song_folder, file)):
                os.rename(os.path.join(song_folder, file), os.path.join(song_folder, f"{song}{file_ending}"))
            else:
                print(f"Could not find file {os.path.join(song_folder, file)}")
                raise FileNotFoundError

        return song_folder

    # Validate all the flags in a txt file and overwrite all that are different to the parameter
    @staticmethod
    def validate_txt_tags(file_path:str, tags:dict[str, str], encoding: str):
        # First read all the lines and get current tags
        current_tags = {}
        with open(file_path, 'r', encoding=encoding) as file:
            lines = file.readlines()
            # Create dict with tag as key and value as value
            current_tags = {line.split(":")[0][1:]:line.split(":")[1] for line in lines if line.startswith("#")}
            content = lines[len(current_tags):]

        # Merge both dicts, tags is dominant and overwrites current_tags if keys match
        new_tags = current_tags | tags

        # Write all new tags to the file and append rest of file
        with open(file_path, 'w',  encoding=encoding) as file:
            file.writelines([f"#{key}:{value}" for key,value in new_tags.items()])
            file.writelines(content)

    # Rename all tags in the txt files to match the files in the directory
    @staticmethod
    def clean_tags(songs_directory:str, song_folder:str):
        tags = {}
        txt = ""
        files = os.listdir(os.path.join(songs_directory, song_folder))
        for file in files:
            # Set the tags to set with validate_txt_tags()
            filetype = os.path.splitext(file)[-1]
            match filetype:
                case (".mp3" | ".mp4"):
                    tags["MP3"] = f"{file}\n"
                    tags["VIDEO"] = f"{file}\n"
                case ".jpg":
                    tags["COVER"] = f"{file}\n"
                case ".txt":
                    txt = file
        try:
            Filesystem.validate_txt_tags(os.path.join(songs_directory, song_folder, txt), tags, "cp1252")
        except:
            # Some song files require using the cp1252-Encoding, while other files require using the utf-8-Encoding instead.
            Filesystem.validate_txt_tags(os.path.join(songs_directory, song_folder, txt), tags, "utf-8")
    @staticmethod
    def remove_duplicates(directory:str, song_list:list[list]) -> list[list]:
        if not os.path.isdir(directory): return song_list
        files_in_directory = os.listdir(directory)
        return [song for song in song_list if song[1] not in files_in_directory]