import datetime
import os

import requests
from dotenv import load_dotenv

from local_group_support.members import get_member_stats

BASE_URL = 'https://organise.earth/'


def get_mattermost_session_token():
    load_dotenv()
    key = os.getenv("MATTERMOST_TOKEN")

    if not key:
        raise OSError('MATTERMOST_TOKEN not found in .env')

    return key


def post_to_channel(channel_id, message):
    data = {"channel_id": channel_id, "message": message}
    headers = {'Authorization': get_mattermost_session_token()}
    response = requests.post(BASE_URL + 'api/v4/posts', headers=headers, json=data)
    return response


if __name__ == "__main__":
    start_date = datetime.date.today() - datetime.timedelta(days=7)
    df = get_member_stats(start_date)
    df_grouped = df.groupby('local_group').size()
    total_signups = df_grouped.sum()
    df_grouped = df_grouped.reset_index().rename(columns={'local_group': 'Local group', 0: '#'})

    message = f"""### Last week's new rebels :star2: 

Hello @all integrators, last week a total of {total_signups} new people became interested in XR and shared their e-mail address to become more involved. Here is a breakdown per-local group

{df_grouped.to_markdown(index=False)}

Let's integrate these rebels into the movement. You can [send them an e-mail](https://docs.google.com/document/d/17vLLVk9VLXmHN7AK3fhYw09AWzhuhwuQFgmG73IoZNk/edit#heading=h.7r56hnx8zumu) inviting them to an upcoming event, or [call them](https://docs.google.com/document/d/17vLLVk9VLXmHN7AK3fhYw09AWzhuhwuQFgmG73IoZNk/edit#heading=h.itfocsvmpr1c) to learn more about how they would like to get involved. You can see more detailed statistics [here](https://docs.google.com/spreadsheets/d/1LrSjkBQqZsIzGKs25O7FC9pHFoOEeRuAAs3IL1NEE8g/edit#gid=709383388) 
For any questions or feedback please send us a message :handshake: """

    post_to_channel('ptcfsqez17dy7r17m4sintgxbc', message)
