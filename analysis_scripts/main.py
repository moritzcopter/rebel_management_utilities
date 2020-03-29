import datetime

from analysis_scripts.forms import get_forms
from analysis_scripts.members import get_member_stats, export_member_stats
from analysis_scripts.messages import export_messages_stats

BACKUP_FILE_PATH = '/Users/pburghardt/Drive/Projekte/xr/rebel_backup/src/backups/backup_rebels_29-03-2020_13:21:33.json'


export_member_stats(BACKUP_FILE_PATH, start_date=datetime.date(2020, 3, 20))
