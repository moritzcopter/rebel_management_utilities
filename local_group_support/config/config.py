import json
from functools import lru_cache


@lru_cache(maxsize=128)
def get_config():
    with open('config/config.json') as file:
        return json.load(file)
