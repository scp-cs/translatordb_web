from os.path import exists
from json import load, dump, JSONDecodeError
from secrets import token_hex

import logging

DEFAULT_CONFIG = {
    "SECRET_KEY": token_hex(24),
    "DEBUG": False
}

def ensure_config(filename: str) -> None:
    if exists(filename):
        try:
            with open(filename) as file:
                _ = load(file)
                logging.info('Config file loaded')
                return
        except JSONDecodeError:
            logging.warning('Config file unreadable, creating new')
            with open(filename, "w") as file:
                dump(DEFAULT_CONFIG, file)
    else:
        logging.warning('Config file not found, creating new')
        with open(filename, "w") as file:
                dump(DEFAULT_CONFIG, file)
    