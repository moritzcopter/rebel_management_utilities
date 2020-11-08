import datetime

from local_group_support.utils.mattermost import post_to_channel, LOGGING_CHANNEL_ID
from rebel_management_utilities.members import get_member_stats
from local_group_support.utils.nextcloud import get_nextcloud_user, BASE_URL, INTEGRATION_DIRECTORY, \
    write_to_spreadsheet

if __name__ == "__main__":
    start_date = datetime.date.today() - datetime.timedelta(days=30)
    df = get_member_stats(start_date)

    for local_group, df_grouped in df.groupby('local_group'):
        try:
            filename = f'New rebels {local_group}.xlsx'
            username = get_nextcloud_user()
            local_group_safe = local_group.replace('/', '').replace(' ', '').replace('â', 'a')
            url = BASE_URL + username + INTEGRATION_DIRECTORY + local_group_safe + '/' + filename
            df_formatted = df_grouped[
                ['name', 'email_address', 'phone_number', 'submission_date', 'municipality', 'sign_up_channel',
                 'taggings']].set_index('submission_date').sort_index()
            df_formatted['next_action'] = 'Contact'
            write_to_spreadsheet(url, df_formatted, deduplicate_column='email_address')
            post_to_channel(LOGGING_CHANNEL_ID, f'Successfully updated integrator spreadsheet for {local_group}')
        except Exception as e:
            post_to_channel(LOGGING_CHANNEL_ID, f'@all Failed to update integrator spreadsheet for {local_group} - {e}')
