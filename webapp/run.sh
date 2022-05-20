#!/bin/sh

# Collect static files and migrate if needed
python /home/api/manage.py collectstatic --noinput
python /home/api/manage.py makemigrations --noinput
python /home/api/manage.py makemigrations api --noinput
python /home/api/manage.py migrate --noinput
python /home/api/manage.py migrate api --noinput

python /home/api/manage.py process_tasks --log-std &

# create a new super user, with username and password 'admin'
echo "from django.contrib.auth import get_user_model
User = get_user_model()
if User.objects.count() == 0:
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
" | python manage.py shell

python /home/load_examples.py &

uwsgi --http-timeout 360s --http :8000 --master --chdir /home/api/  --module core.wsgi
