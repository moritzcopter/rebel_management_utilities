import os

import requests
from dotenv import load_dotenv

API_URL = 'https://actionnetwork.org/api/v2/'


def load_api_key():
    load_dotenv()
    key = os.getenv("ACTION_NETWORK_API_KEY")

    if not key:
        raise OSError('ACTION_NETWORK_API_KEY not found in .env')

    return key


def query(endpoint=None, url=None):
    if url is None:
        url = API_URL + endpoint
    headers = {'OSDI-API-Token': load_api_key()}

    print(f'Querying {url}')
    response = requests.get(url, headers=headers)
    status_code = response.status_code
    if status_code != 200:
        raise requests.HTTPError(response=response)
    return response.json()
