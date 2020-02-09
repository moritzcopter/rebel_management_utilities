from analysis_scripts.forms import get_forms
from analysis_scripts.stats import get_member_stats

BACKUP_FILE_PATH = 'backups/backup_rebels_23-01-2020_23:33:26.json'

# forms = get_forms()
# print(forms)

# messages = get_forms()
# print(messages)

df = get_member_stats(BACKUP_FILE_PATH)
print(df)
df.to_json('member_summary.json')
