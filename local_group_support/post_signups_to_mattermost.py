import datetime

from rebel_management_utilities.members import get_member_stats
from local_group_support.utils.mattermost import post_to_channel

if __name__ == "__main__":
    LOCAL_GROUP_INTEGRATORS_CHANNEL = 'nqs4h6iyrpr3mx4jjy9xqk8i3o'

    start_date = datetime.date.today() - datetime.timedelta(days=30)
    df = get_member_stats(start_date)
    df_grouped = df.groupby('local_group').size()
    total_signups = df_grouped.sum()
    df_grouped = df_grouped.reset_index().rename(columns={'local_group': 'Local group', 0: '#'})

    with open('resources/signups_message.md', 'r') as f:
        message = f.read()

    message = message.format(total_signups=total_signups, signup_table=df_grouped.to_markdown(index=False))

    post_to_channel(LOCAL_GROUP_INTEGRATORS_CHANNEL, message)
