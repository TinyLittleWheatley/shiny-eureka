from datasets import DownloadConfig, load_dataset

from app import config


def load():
    return load_dataset(
        config.DS_NAME,
        split=config.DS_SPLIT,
        download_config=DownloadConfig(),
    )
