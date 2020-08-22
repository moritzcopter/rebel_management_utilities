import pandas as pd

from analysis_scripts.dashboard import pull_from_dashboard, push_to_dashboard
from analysis_scripts.members import export_member_stats
from analysis_scripts.messages import export_messages_stats

UPDATE_DATE_RANGE_NAME = 'Local group dashboard!K28:K28'

result = pull_from_dashboard(range_name=UPDATE_DATE_RANGE_NAME)
last_update_date = pd.to_datetime(result[0][0]).date()

export_member_stats(start_date=last_update_date)
export_messages_stats(start_date=last_update_date)

new_update_date = pd.Timestamp.today().strftime('%Y-%m-%d')
df = pd.DataFrame([new_update_date])
push_to_dashboard(df, range_name=UPDATE_DATE_RANGE_NAME)
