import pandas as pd

from analysis_scripts.config.config import get_config
from analysis_scripts.dashboard import push_to_dashboard
from analysis_scripts.util import query_all


def get_local_group(row):
    for local_group in get_config()['local_groups']:
        if local_group in row['from']:
            return local_group
    return 'Other'


def get_messages():
    messages = query_all(endpoint='messages')
    df = pd.DataFrame(messages)

    def get_stats(row):
        stats = row['statistics']
        if type(stats) is dict:
            return stats
        return {}

    df = pd.concat([df, df.apply(get_stats, axis=1, result_type='expand')], axis=1)

    df['clicked_ratio'] = df['clicked'] / df['opened']
    df['opened_ratio'] = df['opened'] / df['sent']
    df['local_group'] = df.apply(get_local_group, axis=1)
    df['date'] = pd.to_datetime(df['created_date']).dt.date
    return df


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
