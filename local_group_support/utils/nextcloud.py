import os

import requests
from dotenv import load_dotenv

from local_group_support.utils.excel import append_df_to_excel

BASE_URL = 'https://cloud.extinctionrebellion.nl/remote.php/dav/files/'
INTEGRATION_DIRECTORY = '/CloudXRNL/Circles/Integration_Home/Integration_Internal/'


def get_nextcloud_user():
    load_dotenv()
    key = os.getenv("NEXTCLOUD_USER")

    if not key:
        raise OSError('NEXTCLOUD_USER not found in .env')

    return key


def get_nextcloud_password():
    load_dotenv()
    key = os.getenv("NEXTCLOUD_PASSWORD")

    if not key:
        raise OSError('NEXTCLOUD_PASSWORD not found in .env')

    return key


def write_to_spreadsheet(url, data, deduplicate_column=None):
    auth = (get_nextcloud_user(), get_nextcloud_password())
    response = requests.get(url, auth=auth)

    if response.status_code == 200:
        with open('tmp.xlsx', 'wb') as f:
            f.write(response.content)

        append_df_to_excel('tmp.xlsx', data, deduplicate_column=deduplicate_column, header=False)
    else:
        data.to_excel('tmp.xlsx')

    with open('tmp.xlsx', 'rb') as f:
        data = f.read()
        requests.put(url, data=data, auth=auth)
