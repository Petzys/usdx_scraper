import yaml

def load_config(config_file_path:str):
    with open(config_file_path, "r") as file:

        config = yaml.safe_load(file)

    for key in config:
        globals()[key] = config[key]

    globals()["IGNORED_PATTERN"] = ("|").join(config["IGNORED_WORDS"])