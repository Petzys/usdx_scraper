import yaml

def load_config(config_file_path:str) -> dict:
    with open(config_file_path, "r") as file:
        return yaml.safe_load(file)

def update_config(config_file_path:str, config:dict, user_args:dict) -> dict:
    if user_args["user"] and (not config["USDB_USERNAME"] or config["USDB_USERNAME"] is not user_args["user"]): 
        config["USDB_USERNAME"] = user_args["user"]  

    if user_args["password"] and (not config["USDB_PASSWORD"] or config["USDB_PASSWORD"] is not user_args["password"]): 
        config["USDB_PASSWORD"] = user_args["password"]

    if user_args["spotify_id"] and (not config["SPOTIFY_ID"] or config["SPOTIFY_ID"] is not user_args["spotify_id"]): 
        config["SPOTIFY_ID"] = user_args["spotify_id"]

    if user_args["spotify_secret"] and (not config["SPOTIFY_SECRET"] or config["SPOTIFY_SECRET"] is not user_args["spotify_secret"]): 
        config["SPOTIFY_SECRET"] = user_args["spotify_secret"]

    with open(config_file_path, "w") as file:
        yaml.dump(config, file)

    return config

def global_config(config:dict):
    for key in config:
        globals()[key] = config[key]

    globals()["IGNORED_PATTERN"] = ("|").join(config["IGNORED_WORDS"])
