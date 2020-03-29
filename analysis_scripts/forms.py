import pandas as pd

from analysis_scripts.util import query_all


def get_forms():
    forms = query_all(endpoint='forms')

    form_df = []

    for form in forms:
        for identifier in form['identifiers']:
            form_df.append({'name': form['name'],
                            'title': form['title'],
                            'identifier': identifier.split(':')[1],
                            'total_submissions': form['total_submissions'],
                            'browser_url': form['browser_url'],
                            'created_date': form['created_date'],
                            'modified_date': form['modified_date'],
                            'creator': form['_embedded']['osdi:creator']
                            })

    return pd.DataFrame(form_df)
