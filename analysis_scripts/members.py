import datetime
import json

import pandas as pd

from analysis_scripts.dashboard import push_to_dashboard
from analysis_scripts.forms import get_forms
from analysis_scripts.util import query, load_api_key
from rebel_management_utilities import get_all_members

FORMATION_DATE = datetime.date(2018, 4, 1)


def get_form_name(submission, member):
    form_id = submission['action_network:form_id']
    has_website = 'action_network:referrer_data' in submission.keys() and \
                  submission['action_network:referrer_data']['source'] != 'none'
    form_mapping = get_forms().set_index('identifier')['name']

    if form_id not in form_mapping.keys():
        return 'Other'

    form_name = form_mapping[form_id]

    if 'NVDA' in form_name:
        return 'NVDA'

    if 'Volunteer' in form_name:
        return 'Attended introduction meeting'

    if 'Join' in form_name:
        if has_website and pd.to_datetime(member['created_date']).date() < datetime.date(2020, 2, 20):
            return 'Website'
        return 'Attended Talk'

    if 'Website' in form_name:
        return 'Website'

    if 'Join Affinity Group' in form_name:
        return 'Looking for Affinity group'

    return 'Other'


def get_member_forms(member):
    forms = []

    submissions = query(url=member['_links']['osdi:submissions']['href'])

    for submission in submissions['_embedded']['osdi:submissions']:
        forms.append(get_form_name(submission, member))

    return forms


def extract_data(member):
    try:
        local_group = member['custom_fields']['local_group']
    except KeyError:
        local_group = None
    if local_group == 'Not selected' or local_group == 'No group nearby':
        local_group = None
    sign_up_date = pd.to_datetime(member['created_date']).date()
    if sign_up_date < FORMATION_DATE:
        sign_up_date = pd.NaT
    forms = get_member_forms(member)
    return [{'local_group': local_group, 'sign_up_date': sign_up_date, 'sign_up_channel': form} for form in forms]


def get_member_stats(members, start_date):
    members_processed = []
    for m in members[0:-1]:
        print(f'Processing {len(members_processed)} of {len(members)}')
        if pd.to_datetime(m['created_date']).date() <= start_date:
            continue
        members_processed.extend(extract_data(m))

    df = pd.DataFrame(members_processed)
    return df


def export_member_stats(start_date):
    """
    Compiles and pushes member stats to google sheets dashboard
    :param start_date: only members that signed up after this date are exported
    """
    members = get_all_members(api_key=load_api_key())

    df = get_member_stats(members, start_date)
    df_formatted = df[['sign_up_date', 'local_group', 'sign_up_channel']]
    df_formatted['sign_up_date'] = pd.to_datetime(df_formatted['sign_up_date']).dt.strftime('%Y-%m-%d')

    push_to_dashboard(df_formatted, range_name='Raw signup data!A:C')
