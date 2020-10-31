import os

import requests
from dotenv import load_dotenv

BASE_URL = 'https://organise.earth/'


def get_mattermost_session_token():
    load_dotenv()
    key = os.getenv("MATTERMOST_TOKEN")

    if not key:
        raise OSError('MATTERMOST_TOKEN not found in .env')

    return key


def post_to_channel(channel_id, message):
    data = {"channel_id": channel_id, "message": message}
    headers = {'Authorization': get_mattermost_session_token()}
    response = requests.post(BASE_URL + 'api/v4/posts', headers=headers, json=data)
    return response


def get_mattermost_user(email):
    url = BASE_URL + f'/api/v4/users/email/{email}'
    headers = {'Authorization': get_mattermost_session_token()}
    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        return response.json()
