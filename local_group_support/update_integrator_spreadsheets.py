import datetime

from local_group_support.utils.mattermost import post_to_channel, LOGGING_CHANNEL_ID
from rebel_management_utilities.members import get_member_stats
from local_group_support.utils.nextcloud import get_nextcloud_user, BASE_URL, INTEGRATION_DIRECTORY, \
    write_to_spreadsheet

if __name__ == "__main__":
    start_date = datetime.date.today() - datetime.timedelta(days=30)
    df = get_member_stats(start_date)

    df_filtered = df[(df['sign_up_date'] > start_date) | (df['form_name'].str.contains('Introduction session'))]

    for local_group, df_grouped in df_filtered.groupby('local_group'):
        try:
            filename = f'New rebels {local_group}.xlsx'
            username = get_nextcloud_user()
            local_group_safe = local_group.replace('/', '').replace(' ', '').replace('â', 'a')
            url = BASE_URL + username + INTEGRATION_DIRECTORY + local_group_safe + '/' + filename

            df_formatted = df_grouped[['name', 'submission_date', 'email_address', 'phone_number', 'form_name',
                                       'municipality', 'taggings', 'comments']].sort_values('submission_date')

            df_formatted['next_action'] = 'Contact'
            df_formatted['last_contacted'] = ''

            df_formatted = df_formatted.rename(columns={'name': 'Naam', 'email_address': 'E-mail',
                                                        'phone_number': 'Telefoon', 'municipality': 'Gemeente',
                                                        'form_name': 'Aangemeld via', 'taggings': 'Interesses',
                                                        'last_contacted': 'laatst gecontacteerd',
                                                        'submission_date': 'datum',
                                                        'next_action': 'Volgende actie', 'comments': 'Commentaar'})

            write_to_spreadsheet(url, df_formatted, deduplicate_column='E-mail')
            post_to_channel(LOGGING_CHANNEL_ID, f'Successfully updated integrator spreadsheet for {local_group}')
        except Exception as e:
            post_to_channel(LOGGING_CHANNEL_ID, f'@all Failed to update integrator spreadsheet for {local_group} - {e}')
