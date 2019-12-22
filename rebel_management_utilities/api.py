import os
from dotenv import load_dotenv
import requests

__all__ = ['load_api_key', 'get_all_members']


def load_api_key():
    load_dotenv()
    key = os.getenv("ACTION_NETWORK_API_KEY")

    if not key:
        raise OSError('ACTION_NETWORK_API_KEY not found in environment variables')


def get_all_members():
    url = 'https://actionnetwork.org/api/v2/people'
    members = []

    key = load_api_key()
    headers = {'OSDI-API-Token': key}

    while True:
        response = requests.get(url, headers=headers)
        status_code = response.status_code
        if status_code != 200:
            raise requests.HTTPError(response=response)
        content = response.json()
        new_members = content['_embedded']['osdi:people']
        members.extend(new_members)
        try:
            url = content['_links']['next']['href']
        except KeyError:  # end querying data when there is no more data left
            break

    return members
