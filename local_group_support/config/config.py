import json
import pathlib
from functools import lru_cache


@lru_cache(maxsize=128)
def get_config():
    with open(pathlib.Path(__file__).parent / 'config.json') as file:
        return json.load(file)
