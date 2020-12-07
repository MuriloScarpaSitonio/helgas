release: python manage.py migrate
web: gunicorn PeanutButter.wsgi --log-file - --bind 0.0.0.0:$PORT