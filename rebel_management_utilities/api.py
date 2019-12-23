import requests

__all__ = ['get_all_members']


def get_all_members(api_key):
    url = 'https://actionnetwork.org/api/v2/people'
    headers = {'OSDI-API-Token': api_key}

    members = []

    while True:
        response = requests.get(url, headers=headers)
        status_code = response.status_code
        if status_code != 200:
            raise requests.HTTPError(response=response)
        content = response.json()
        new_members = content['_embedded']['osdi:people']
        members.extend(new_members)
        try:
            url = content['_links']['next']['href']
        except KeyError:  # end querying when there is no more data left
            break

    return members
