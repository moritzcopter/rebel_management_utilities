import datetime

import pandas as pd

from local_group_support.utils.google import export_messages_stats, pull_from_dashboard, export_member_stats

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1LrSjkBQqZsIzGKs25O7FC9pHFoOEeRuAAs3IL1NEE8g'
UPDATE_DATE_RANGE_NAME = 'Local group dashboard!K28:K28'

if __name__ == "__main__":
    export_messages_stats(start_date=datetime.date(2017, 1, 1))

    result = pull_from_dashboard(range_name=UPDATE_DATE_RANGE_NAME)
    last_update_date = pd.to_datetime(result[0][0]).date()

    export_member_stats(start_date=last_update_date)
    export_messages_stats(start_date=last_update_date)
