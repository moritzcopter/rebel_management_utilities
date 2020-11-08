import datetime

from local_group_support.utils.mattermost import post_to_channel, LOGGING_CHANNEL_ID
from rebel_management_utilities.members import get_member_stats
from local_group_support.utils.nextcloud import get_nextcloud_user, BASE_URL, INTEGRATION_DIRECTORY, \
    write_to_spreadsheet

if __name__ == "__main__":
    try:
        start_date = datetime.date.today() - datetime.timedelta(days=10)
        df = get_member_stats(start_date)

        for local_group, df_grouped in df.groupby('local_group'):
            filename = f'New rebels {local_group}.xlsx'
            username = get_nextcloud_user()
            url = BASE_URL + username + INTEGRATION_DIRECTORY + filename
            df_formatted = df_grouped[
                ['submission_date', 'municipality', 'sign_up_channel']].set_index('submission_date')
            write_to_spreadsheet(url, df_formatted, deduplicate_column='submission_date')

        post_to_channel(LOGGING_CHANNEL_ID, 'Successfully updated integrator spreadsheets')
    except Exception as e:
        post_to_channel(LOGGING_CHANNEL_ID, f'Failed to update integrator spreadsheet - {e}')
