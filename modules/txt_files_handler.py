# Validate all the flags in a txt file and overwrite all that are different to the parameter
import os

def validate_txt_tags(file_path:str, tags:dict[str, str]):
    # First read all the lines and get current tags
    current_tags = {}
    with open(file_path, 'r', encoding='cp1252') as file:
        lines = file.readlines();
        # Create dict with tag as key and value as value
        current_tags = {line.split(":")[0][1:]:line.split(":")[1] for line in lines if line.startswith("#")}
        content = lines[len(current_tags):]

    # Merge both dicts, tags is dominant and overwrites current_tags if keys match
    new_tags = current_tags | tags

    # Write all new tags to the file and append rest of file
    with open(file_path, 'w',  encoding='utf-8') as file:
        file.writelines([f"#{key}:{value}" for key,value in new_tags.items()])
        file.writelines(content)

# Rename all tags in the txt files to match the files in the directory
def clean_tags(songs_directory:str, song_folder:str):
    tags = {}
    files = os.listdir(os.path.join(songs_directory, song_folder))
    for file in files:
        # Set the tags to set with validate_txt_tags()
        filetype = os.path.splitext(file)[-1]
        match filetype:
            case ".mp3":
                tags["MP3"] = f"{file}\n"
                tags["VIDEO"] = f"{file}\n"
            case ".jpg":
                tags["COVER"] = f"{file}\n"
            case ".txt":
                txt = file
    validate_txt_tags(os.path.join(songs_directory, song_folder, txt), tags)

def remove_duplicates(directory:str, song_list:str) -> list[list]:
    if not os.path.isdir(directory): return song_list
    files_in_directory = os.listdir(directory)
    return [song for song in song_list if song[1] not in files_in_directory]