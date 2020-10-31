import datetime

from local_group_support.utils.members import get_member_stats
from local_group_support.utils.mattermost import post_to_channel

if __name__ == "__main__":
    LOCAL_GROUP_INTEGRATORS_CHANNEL = 'nqs4h6iyrpr3mx4jjy9xqk8i3o'

    start_date = datetime.date.today() - datetime.timedelta(days=30)
    df = get_member_stats(start_date)
    df_grouped = df.groupby('local_group').size()
    total_signups = df_grouped.sum()
    df_grouped = df_grouped.reset_index().rename(columns={'local_group': 'Local group', 0: '#'})

    message = f"""### Last month's new rebels :star2: 

Hello @all integrators, last month a total of {total_signups} new people became interested in XR and shared their e-mail address to become more involved. Here is a breakdown per-local group

{df_grouped.to_markdown(index=False)}

Let's integrate these rebels into the movement. You can [send them an e-mail](https://docs.google.com/document/d/17vLLVk9VLXmHN7AK3fhYw09AWzhuhwuQFgmG73IoZNk/edit#heading=h.7r56hnx8zumu) inviting them to an upcoming event, or [call them](https://docs.google.com/document/d/17vLLVk9VLXmHN7AK3fhYw09AWzhuhwuQFgmG73IoZNk/edit#heading=h.itfocsvmpr1c) to learn more about how they would like to get involved. You can see more detailed statistics [here](https://docs.google.com/spreadsheets/d/1LrSjkBQqZsIzGKs25O7FC9pHFoOEeRuAAs3IL1NEE8g/edit#gid=709383388) 
For any questions or feedback please send us a message :handshake: """

    post_to_channel(LOCAL_GROUP_INTEGRATORS_CHANNEL, message)
