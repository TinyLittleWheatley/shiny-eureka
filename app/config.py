from os import getenv


def ge(name):
    val = getenv(name)
    if not val:
        raise Exception(f"Env var {name} is not set or blank")

    return val


DS_NAME = ge("DS_NAME")
DS_SPLIT = ge("DS_SPLIT")
AUDIO_DIR = getenv("AUDIO_DIR", "audio_cache")
ASSETS_DIR = getenv("ASSETS_DIR", "app/web")
