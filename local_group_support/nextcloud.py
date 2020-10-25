import os

import pandas as pd
import requests
from dotenv import load_dotenv

BASE_URL = 'https://cloud.extinctionrebellion.nl/remote.php/dav/files/'


def get_nextcloud_user():
    load_dotenv()
    key = os.getenv("NEXTCLOUD_USEr")

    if not key:
        raise OSError('NEXTCLOUD_USER not found in .env')

    return key


def get_nextcloud_password():
    load_dotenv()
    key = os.getenv("NEXTCLOUD_PASSWORD")

    if not key:
        raise OSError('NEXTCLOUD_PASSWORD not found in .env')

    return key


def append_to_spreadsheet(data, url):
    auth = (get_nextcloud_user(), get_nextcloud_password())
    response = requests.get(url, auth=auth)

    with open('tmp.xlsx', 'wb') as f:
        f.write(response.content)

    df = pd.read_excel('tmp.xlsx').append(data)
    df.to_excel('tmp.xlsx')

    with open('tmp.xlsx', 'rb') as f:
        data = f.read()
        requests.put(url, data=data, auth=auth)
