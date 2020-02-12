import pandas as pd

from analysis_scripts.util import query


def get_messages():
    res = query(endpoint='messages')
    messages = res['_embedded']['osdi:messages']

    df = []
    for message in messages:
        df.append(message)
    df = pd.DataFrame(df)

    def get_stats(row):
        return row['statistics']

    df = pd.concat([df, df.apply(get_stats, axis=1, result_type='expand')], axis=1)

    df['clicked_ratio'] = df['clicked'] / df['opened']
    df['opened_ratio'] = df['opened'] / df['sent']

    return df
