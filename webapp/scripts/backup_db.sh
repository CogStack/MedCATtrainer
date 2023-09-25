#!/bin/sh

BACKUP_DIR=${DB_BACKUP_DIR}

# assumes DB dir is ../api/db/db.sqlite3
# this should mirror what's in api/settings.py DATABASES['default']
DB_FILE=/home/api/db/db.sqlite3

if [ -n "${BACKUP_DIR}" ]; then
  echo "Found backup dir location: ${BACKUP_DIR}"
  if [ ! -d "${BACKUP_DIR}" ]; then
    mkdir BACKUP_DIR
  fi
  BACKUP_NAME=db-backup-$(date +"%Y-%m-%d__%H-%M-%S").sqlite3
  cp $DB_FILE ./${BACKUP_DIR}/${BACKUP_NAME}
  echo "Backed up existing DB to ./${BACKUP_DIR}/${BACKUP_NAME}"
  echo "To restore this backup use $ source ./restore.sh ./${BACKUP_DIR}/${BACKUP_NAME}"
else
  echo "No BACKUP_DIR env var found. This should be set in env vars. No backups will be created"
  return 0
fi
