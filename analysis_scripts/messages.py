import pandas as pd

from analysis_scripts.config.config import get_config
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
