import pandas as pd

from analysis_scripts.util import query_all

LOCAL_GROUPS = [
    "Amsterdam",
    "Arnhem/Nijmegen",
    "Brabant",
    "Castricum",
    "Delft",
    "Den Haag",
    "Deventer",
    "Enschede",
    "Groningen",
    "Haarlem",
    "Leeuwarden/Fryslân",
    "Leiden",
    "Maastricht",
    "Roermond",
    "Rotterdam",
    "Utrecht",
    "Wageningen",
    "Ysselvallei",
    "Zaandam",
    "Zwolle"]


def get_local_group(row):
    for local_group in LOCAL_GROUPS:
        if local_group in row['from']:
            return local_group


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


def export_messages_stats(export_filename='messages.csv'):
    """
    Compiles and saves email stats
    To update local groups stats google spreadsheet run this and replace the hidden raw email email data sheet
    (View > hidden sheets) with output (File > Import > Upload > Replace current sheet)
    Afterwards, hide the raw email data sheet (right click sheet > Hide sheet)
    Sheet URL: https://docs.google.com/spreadsheets/d/1LrSjkBQqZsIzGKs25O7FC9pHFoOEeRuAAs3IL1NEE8g/edit#gid=709383388
    """
    df = get_messages()
    df = df[df['sent'] > 0]
    df_formatted = df.sort_values('date', ascending=True)[
        ['date', 'local_group', 'from', 'subject', 'sent', 'clicked', 'opened', 'bounced',
         'unsubscribed', 'clicked_ratio', 'opened_ratio']].set_index('date')

    df_formatted.to_csv(export_filename)
