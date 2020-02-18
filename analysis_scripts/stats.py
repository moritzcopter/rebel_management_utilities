import json

import pandas as pd

from analysis_scripts.forms import get_forms
from analysis_scripts.util import query


def extract_primary_email(row):
    emails = row['email_addresses']
    for email in emails:
        if email['primary']:
            return email['address']


def extract_primary_locality(row):
    addresses = row['postal_addresses']
    for address in addresses:
        if address['primary']:
            if 'locality' in address.keys():
                return address['locality']
            elif 'region' in address.keys():
                return address['region']
            else:
                return


def extract_primary_postal_code(row):
    addresses = row['postal_addresses']
    for address in addresses:
        if address['primary']:
            return address['postal_code']


def to_str(row, col):
    return str(row[col])


def extract_signup_form(submissions):
    if len(submissions['_embedded']['osdi:submissions']) < 1:
        return None, None
    signup_submission = submissions['_embedded']['osdi:submissions'][0]
    form_id = signup_submission['action_network:form_id']
    if 'action_network:referrer_data' in signup_submission.keys():
        return form_id, signup_submission['action_network:referrer_data']['source']
    return form_id, None


def get_sign_up_channel(member):
    submissions = query(url=member['_links']['osdi:submissions']['href'])
    return extract_signup_form(submissions)


def extract_data(member):
    try:
        local_group = member['custom_fields']['local_group']
    except KeyError:
        local_group = None
    if local_group == 'Not selected' or local_group == 'No group nearby':
        local_group = None
    sign_up_datetime = member['created_date']
    sign_up_date = sign_up_datetime.split('T')[0]
    sign_up_form, sign_up_website = get_sign_up_channel(member)
    return {'local_group': local_group, 'sign_up_date': sign_up_date, 'sign_up_form': sign_up_form,
            'sign_up_website': sign_up_website}


def map_signup_form(row, form_mapping):
    signup_form = 'Other'

    if row['sign_up_form'] is None or row['sign_up_form'] not in form_mapping.keys():
        return signup_form

    return form_mapping[row['sign_up_form']]


def get_member_stats(backup_file_path):
    with open(backup_file_path) as f:
        members = json.load(f)['members']

    members_processed = []
    for m in members[0:-1]:
        print(f'Processing {len(members_processed)} of {len(members)}')
        members_processed.append(extract_data(m))

    df = pd.DataFrame(members_processed)

    form_mapping = get_forms().set_index('identifier')['title']
    df['form_name'] = df.apply(map_signup_form, form_mapping=form_mapping, axis=1)
    df['has_website'] = (~df['sign_up_website'].isin(['none', None]))
    df['is_introduction_meeting_signup'] = (~df['has_website'] & df['form_name'].isin(
        ['Volunteer at Extinction Rebellion NL', 'Doe mee bij Extinction Rebellion NL']))

    return df
