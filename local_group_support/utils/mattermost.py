import os

import requests
from dotenv import load_dotenv

BASE_URL = 'https://organise.earth/'
LOGGING_CHANNEL_ID = 'gg3tdykut7f97xmg5kfpez7fuo'  # "Action Network Developers" private channel (xrNetherlands)
LOCAL_GROUP_INTEGRATORS_CHANNEL_ID = 'nqs4h6iyrpr3mx4jjy9xqk8i3o'  # "Local Group Integrators" private channel (xrNetherlands)


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
