import datetime

import pandas as pd

from local_group_support.config.config import get_config
from local_group_support.forms import get_forms
from local_group_support.util import query, query_all

FORMATION_DATE = datetime.date(2018, 4, 1)


def get_form(submission):
    form_id = submission['action_network:form_id']
    has_website = 'action_network:referrer_data' in submission.keys() and \
                  submission['action_network:referrer_data']['source'] != 'none'
    form_mapping = get_forms().set_index('identifier')['name']
    submission_date = pd.to_datetime(submission['created_date']).date()

    form_name = 'Other'
    sign_up_channel = 'Other'

    if form_id in form_mapping.keys():
        form_name = form_mapping[form_id]

    if 'NVDA' in form_name:
        sign_up_channel = 'NVDA'

    if 'Volunteer' in form_name:
        sign_up_channel = 'Attended introduction meeting'

    if 'Join' in form_name:
        if has_website and submission_date < datetime.date(2020, 2, 20):
            sign_up_channel = 'Website'
        else:
            sign_up_channel = 'Attended Talk'

    if 'Website' in form_name:
        sign_up_channel = 'Website'

    if 'Join Affinity Group' in form_name:
        sign_up_channel = 'Looking for Affinity group'

    return {'form_name': form_name, 'sign_up_channel': sign_up_channel, 'form_id': form_id,
            'submission_date': submission_date}


def get_member_forms(member):
    submissions = query(url=member['_links']['osdi:submissions']['href'])

    forms = []
    for submission in submissions['_embedded']['osdi:submissions']:
        forms.append(get_form(submission))

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
             **form} for form in forms]


def get_member_stats(start_date):
    members = query_all(endpoint='people')

    members_processed = []

    for index, m in enumerate(members):
        print(f'Processing {index} of {len(members)}')
        if pd.to_datetime(m['created_date']).date() <= start_date:
            continue
        members_processed.extend(extract_data(m))

    df = pd.DataFrame(members_processed)
    return df
