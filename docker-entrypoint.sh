#!/bin/sh
# Runs on every container start, before the web server.
#
# Migrations must run here rather than at image build time: the build step runs
# against the image filesystem with no database connection, so a migrate at
# build either no-ops or fails silently behind "|| true". Running it here means
# it happens against the real DATABASE_URL every time the container starts.
set -e

python manage.py migrate --noinput

# Recreates the superuser and, with the flag, the staff and customer accounts
# plus sample genres, tags, songs and a playlist. Idempotent.
python manage.py ensure_admin --with-demo

exec gunicorn yum_jukebox.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${WEB_CONCURRENCY:-2}" \
    --access-logfile -
