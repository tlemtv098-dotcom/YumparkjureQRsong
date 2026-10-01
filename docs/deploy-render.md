# Deploying to Render

The hosted site is `https://yumpakjure.onrender.com/`.

## Why the database is the important part

With no `DATABASE_URL` the project falls back to SQLite on the container's own
disk. Render replaces that disk on every deploy, so the database is wiped and
the site comes back empty. Two things depend on this:

- Accounts and demo data are recreated at startup by
  `python manage.py ensure_admin --with-demo`.
- Logged-in sessions are stored in the database, so every deploy also logs
  everyone out.

Setting `DATABASE_URL` to a real Postgres fixes both.

## Required environment variables

| Variable | Value |
|----------|-------|
| `SECRET_KEY` | a private random string. Generate one with:<br>`python manage.py shell -c "from django.core.management.utils import get_random_secret_key as k; print(k())"` |
| `DATABASE_URL` | Render's **Internal Database URL**, copied from the Postgres addon's connection string |
| `DATABASE_SSL_REQUIRE` | `False` for Render's internal Postgres, which does not use TLS. Set `True` only for a managed host that requires it. |
| `DEBUG` | `False` |
| `PLAYER_TOKEN` | any private random string; the player page sends it as `X-Player-Token` for owner rights on the queue and block APIs |

`YOUTUBE_API_KEY` is optional but the search endpoint returns nothing without it.

## Required start command

Render's default start command does not run migrations, so the database is never
prepared and the accounts are never created. Set **Settings > Build & Deploy >
Start Command** to:

```
python manage.py migrate --noinput && python manage.py ensure_admin --with-demo && gunicorn yum_jukebox.wsgi:application --bind 0.0.0.0:$PORT --workers 2
```

The `Procfile` in the repository root holds the same line. Render only uses it
when no start command is set in the dashboard, so set it explicitly.

Order matters: migrate creates the tables, `ensure_admin` needs those tables to
give the superuser a `Profile` row, and gunicorn starts last.

## If the site comes back and nobody can log in

That means `ensure_admin` did not run, which happens when the start command was
never set. Either set it and redeploy, or run it once by hand from the
dashboard's Shell tab:

```
python manage.py ensure_admin --with-demo
```

## Uploaded media is not durable

Uploads land on the container's disk and disappear on redeploy, for the same
reason the SQLite data does. A real deployment would point `MEDIA_ROOT` at
object storage. The media route in `yum_jukebox/urls.py` is a guarded Django
view rather than object storage precisely so this project needs no paid
service to demonstrate the upload criterion.
