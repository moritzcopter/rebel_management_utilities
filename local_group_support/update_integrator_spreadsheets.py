import datetime

from local_group_support.config.config import get_config
from local_group_support.utils.mattermost import post_to_channel, LOGGING_CHANNEL_ID
from rebel_management_utilities.members import get_member_stats
from local_group_support.utils.nextcloud import get_nextcloud_user, BASE_URL, INTEGRATION_DIRECTORY, \
    write_to_spreadsheet, CIRCLE_INTEGRATION_DIRECTORY


def get_spreadsheet_url(base_directory, group):
    username = get_nextcloud_user()
    group_safe = ''.join(e for e in group if e.isalnum()).replace('â', 'a')
    filename = f'New rebels {group_safe}.xlsx'
    return BASE_URL + username + base_directory + group_safe + '/' + filename


def push_spreadsheet(df, group, base_directory):
    try:
        url = get_spreadsheet_url(base_directory, group)
        df_formatted = df[['submission_date', 'name', 'email_address', 'phone_number', 'municipality',
                           'form_name', 'taggings', 'comments']].sort_values('submission_date')

        df_formatted = df_formatted.rename(columns={'name': 'Naam', 'email_address': 'E-mail',
                                                    'phone_number': 'Telefoon', 'municipality': 'Gemeente',
                                                    'form_name': 'Aangemeld via', 'taggings': 'Interesses',
                                                    'submission_date': 'Aangemeld op', 'comments': 'Commentaar'})

        write_to_spreadsheet(url, df_formatted, deduplicate_column='E-mail')
        post_to_channel(LOGGING_CHANNEL_ID,
                        f'Successfully updated integrator spreadsheet for {group} - {len(df_formatted)} new rebels')
    except Exception as e:
        post_to_channel(LOGGING_CHANNEL_ID, f'@all Failed to update integrator spreadsheet for {group} - {e}')


if __name__ == "__main__":
    start_date = datetime.date.today() - datetime.timedelta(days=30)
    df = get_member_stats(start_date)
    df_filtered = df[(df['sign_up_date'] > start_date) | (df['form_name'].str.contains('Introduction session'))]

    for local_group, df_grouped in df_filtered.groupby('local_group'):
        push_spreadsheet(df_grouped, local_group, INTEGRATION_DIRECTORY)

    for circle, circle_config in get_config()['circles'].items():
        df_grouped = df_filtered[df_filtered['taggings'].apply(lambda x: circle_config["tagging"] in x)]
        push_spreadsheet(df_grouped, circle, CIRCLE_INTEGRATION_DIRECTORY)
