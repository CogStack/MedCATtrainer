#!/bin/sh

# run db backup script before doing anything
/home/scripts/backup_db.sh

# env vars that should only be on for app running...
TMP_RESUBMIT_ALL_VAR=$RESUBMIT_ALL_ON_STARTUP
export RESUBMIT_ALL_ON_STARTUP=0

# Collect static files and migrate if needed
python /home/api/manage.py collectstatic --noinput
python /home/api/manage.py makemigrations --noinput
python /home/api/manage.py makemigrations api --noinput
python /home/api/manage.py migrate --noinput
python /home/api/manage.py migrate api --noinput

python /home/api/manage.py process_tasks --log-std &

# create a new super user, with username and password 'admin'
# also create a user group `user_group` that prevents users from deleting models
echo "from django.contrib.auth import get_user_model
from django.contrib.auth.models import User, Group, Permission
User = get_user_model()
if User.objects.count() == 0:
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
group, created = Group.objects.get_or_create(name='user_group')
if created:
    user = User.objects.create_user('username', 'username@example.com', 'password')
    group.user_set.add(user)
    permissions = Permission.objects.exclude(codename__contains='delete')
    for p in permissions:
      group.permissions.add(p)
" | python manage.py shell

if [ $LOAD_EXAMPLES ]; then
  python /home/scripts/load_examples.py &
fi

# RESET any Env vars to original stat
export RESUBMIT_ALL_ON_STARTUP=$TMP_RESUBMIT_ALL_VAR

uwsgi --http-timeout 360s --http :8000 --master --chdir /home/api/  --module core.wsgi
