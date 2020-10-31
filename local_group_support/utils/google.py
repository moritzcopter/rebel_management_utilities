from __future__ import print_function

import pickle
from functools import lru_cache

import pandas as pd
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from local_group_support.utils.action_network import get_messages
from local_group_support.utils.members import get_member_stats

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1LrSjkBQqZsIzGKs25O7FC9pHFoOEeRuAAs3IL1NEE8g'


@lru_cache(maxsize=128)
def get_service():
    creds = None
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    service = build('sheets', 'v4', credentials=creds)
    return service


def push_to_dashboard(df, range_name):
    service = get_service()

    values = df.values.tolist()
    body = {
        'values': values
    }

    result = service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID, range=range_name,
        valueInputOption='USER_ENTERED', body=body).execute()
    print('{0} cells appended.'.format(result \
                                       .get('updates') \
                                       .get('updatedCells')))


def pull_from_dashboard(range_name):
    service = get_service()

    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=range_name).execute()
    rows = result.get('values', [])
    print('{0} rows retrieved.'.format(len(rows)))
    return rows


def export_member_stats(start_date):
    """
    Compiles and pushes member stats to google sheets dashboard
    :param start_date: only members that signed up after this date are exported
    """

    df = get_member_stats(start_date)
    df_formatted = df[['sign_up_date', 'local_group', 'sign_up_channel']].sort_values('sign_up_date')
    df_formatted['sign_up_date'] = pd.to_datetime(df_formatted['sign_up_date']).dt.strftime('%Y-%m-%d')
    df_formatted = df_formatted.fillna('')

    push_to_dashboard(df_formatted, range_name='Raw signup data!A:C')


def export_messages_stats(start_date):
    """
    Compiles and pushes email stats to google sheets dashboard
    Sheet URL: https://docs.google.com/spreadsheets/d/1LrSjkBQqZsIzGKs25O7FC9pHFoOEeRuAAs3IL1NEE8g/edit#gid=709383388
    :param start_date: only messages after this date are exported
    """
    df = get_messages()
    df = df[df['sent'] > 0]
    df_formatted = df.sort_values('date', ascending=True)[
        ['date', 'local_group', 'from', 'subject', 'sent', 'clicked', 'opened', 'bounced',
         'unsubscribed', 'clicked_ratio', 'opened_ratio']]
    df_formatted = df_formatted[df_formatted['date'] >= start_date]
    df_formatted['date'] = pd.to_datetime(df_formatted['date']).dt.strftime('%Y-%m-%d')
    df_formatted = df_formatted.fillna(0.0)

    push_to_dashboard(df_formatted, range_name='Raw email data!A:K')
