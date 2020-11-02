import datetime

from rebel_management_utilities.members import get_member_stats
from local_group_support.utils.nextcloud import get_nextcloud_user, BASE_URL, INTEGRATION_DIRECTORY, \
    write_to_spreadsheet

if __name__ == "__main__":
    start_date = datetime.date.today() - datetime.timedelta(days=3)
    df = get_member_stats(start_date)

    for local_group, df_grouped in df.groupby('local_group'):
        filename = f'New rebels {local_group}.xlsx'
        username = get_nextcloud_user()
        url = BASE_URL + username + INTEGRATION_DIRECTORY + filename
        write_to_spreadsheet(url, df_grouped[
            ['submission_date', 'municipality', 'sign_up_channel']].set_index('submission_date'))
