import datetime
import json

import pandas as pd

from analysis_scripts.config.config import get_config
from analysis_scripts.dashboard import push_to_dashboard
from analysis_scripts.forms import get_forms
from analysis_scripts.mattermost import post_to_channel
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


def get_custom_field(member, field):
    value = None
    if field in member['custom_fields']:
        value = member['custom_fields'][field]
    return value


def get_local_group(member):
    local_group = get_custom_field(member, 'local_group')

    if local_group == 'Not selected' or local_group == 'No group nearby':
        local_group = None

    if not local_group:
        municipality = get_custom_field(member, 'Municipality')
        config = get_config()
        for _local_group, local_group_config in config['local_groups'].items():
            if municipality in local_group_config['municipalities']:
                local_group = _local_group
                break
    return local_group


def extract_data(member):
    sign_up_date = pd.to_datetime(member['created_date']).date()
    if sign_up_date < FORMATION_DATE:
        sign_up_date = pd.NaT
    forms = get_member_forms(member)
    local_group = get_local_group(member)
    municipality = get_custom_field(member, 'Municipality')
    return [{'local_group': local_group, 'municipality': municipality, 'sign_up_date': sign_up_date,
             'sign_up_channel': form} for form in forms]



def get_member_stats(start_date):
    members = get_all_members(api_key=load_api_key())

    members_processed = []

    for index, m in enumerate(members):
        print(f'Processing {index} of {len(members)}')
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

    df = get_member_stats(start_date)
    df_formatted = df[['sign_up_date', 'local_group', 'sign_up_channel']]
    df_formatted['sign_up_date'] = pd.to_datetime(df_formatted['sign_up_date']).dt.strftime('%Y-%m-%d')

    push_to_dashboard(df_formatted, range_name='Raw signup data!A:C')