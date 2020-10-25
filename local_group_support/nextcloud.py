import datetime
import os

import pandas as pd
import requests
from dotenv import load_dotenv

from local_group_support.members import get_member_stats

BASE_URL = 'https://cloud.extinctionrebellion.nl/remote.php/dav/files/'
DIRECTORY = '/CloudXRNL/Circles/Integration_Home/Integration_Internal/'


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


def write_to_spreadsheet(url, data):
    auth = (get_nextcloud_user(), get_nextcloud_password())
    response = requests.get(url, auth=auth)

    if response.status_code == 200:
        with open('tmp.xlsx', 'wb') as f:
            f.write(response.content)

        df = pd.read_excel('tmp.xlsx').append(data)
        df.to_excel('tmp.xlsx')
    else:
        data.to_excel('tmp.xlsx')

    with open('tmp.xlsx', 'rb') as f:
        data = f.read()
        requests.put(url, data=data, auth=auth)


if __name__ == "__main__":
    start_date = datetime.date.today() - datetime.timedelta(days=1)
    df = get_member_stats(start_date)

    for local_group, df_grouped in df.groupby('local_group'):
        filename = f'New members {local_group}.xlsx'
        username = get_nextcloud_user()
        url = BASE_URL + username + DIRECTORY + filename
        write_to_spreadsheet(url, df_grouped)
