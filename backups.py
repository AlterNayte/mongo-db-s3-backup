import os
import boto3
from dotenv import load_dotenv
from datetime import date, datetime

load_dotenv()

# setup
session = boto3.session.Session()
client = session.client('s3',
                        region_name='fra1',
                        endpoint_url='https://fra1.digitaloceanspaces.com',
                        aws_access_key_id=os.getenv('SPACES_KEY'),
                        aws_secret_access_key=os.getenv('SPACES_SECRET'))

user_str = f"--username {os.getenv('MONGODB_USER')}"
pass_str = f" --password {os.getenv('MONGODB_PASS')}"
db_str = f" --db {os.getenv('MONGODB_DB')}" if os.getenv('MONGODB_DB') else ""
op_log_option = "" if os.getenv('MONGODB_DB') else ""
timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%S')
backup_name = f"{timestamp}.dump.gz"
latest_name = f"latest.dump.gz"
backup = f"{os.getenv('BACKUP_FOLDER')}{backup_name}"
backup_latest = f"{os.getenv('BACKUP_FOLDER')}{latest_name}"


def old_backups(backup):
  if 'latest' in backup['Key']:
    return False
  else:
    return True

def delete_backup(key):
  client.delete_object(Bucket=os.getenv('SPACE_NAME'), Key=key)

def restore_latest():
  client.download_file(os.getenv('SPACE_NAME'), backup_latest, latest_name)
  restore_command = f"mongorestore --host {os.getenv('MONGODB_HOST')} --port {os.getenv('MONGODB_PORT')} \
  {user_str}{pass_str}{db_str} --archive={latest_name} --gzip --drop"

  os.system(restore_command)

  cleanup_command = f"rm {latest_name}"
  os.system(cleanup_command)
  quit()

def run_backup():
  print('Starting backup...')
  # Run backup command
  command = f"mongodump --host {os.getenv('MONGODB_HOST')} --port {os.getenv('MONGODB_PORT')} \
  {user_str}{pass_str}{db_str} --archive={backup_name} --gzip {op_log_option} {os.getenv('EXTRA_OPTS')}"
  print(command)
  os.system(command)


  # Upload backups
  client.upload_file(backup_name, os.getenv('SPACE_NAME'), backup)
  client.upload_file(backup_name, os.getenv('SPACE_NAME'), backup_latest)

  
  response = client.list_objects(Bucket=os.getenv('SPACE_NAME'))
  verified = False
  # Verify new backups are saved to s3 storage.
  for obj in response['Contents']:
    if backup == obj['Key']:
      verified = True

  if verified:
    print('Backup successfully verified.')
    # Delete old backups
    response = client.list_objects(Bucket=os.getenv('SPACE_NAME'))
    try:
      backups_to_keep = int(os.getenv('BACKUP_COPIES',3))

      # Filter the list of backups so that we keep X count of backups along with the one named latest
      backups = list(filter(old_backups,response['Contents']))

      # Sort backups by date in descending order, newest to oldest
      backups.sort(key=lambda x: x['LastModified'], reverse=True)
      backups_to_keep = backups[:backups_to_keep]
      for b in backups:
        if b not in backups_to_keep:
          print(f"Deleting backup {b['Key']}")
          delete_backup(b['Key'])
    except KeyError:
        print('No files in space')
    finally:
      print('Backup process completed.')
  else:
    print('Backup was not completed successfully. Please check storage location.')
  quit()

if os.getenv('MODE') == "restore":
  restore_latest()
else:
  run_backup()
