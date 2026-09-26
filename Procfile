web: python manage.py migrate --noinput && python manage.py ensure_admin && gunicorn yum_jukebox.wsgi:application --bind 0.0.0.0:$PORT --workers 2
