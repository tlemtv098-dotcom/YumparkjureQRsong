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

## How this service starts

This service is deployed as a **Docker** image, so Render ignores a `Procfile`
entirely. Two things follow from that, and both have bitten this project:

- The **Docker Command** field under Settings > Build & Deploy is **not a shell**.
  It replaces the image entrypoint as an argument list, so a shell operator like
  `&&` is passed straight through as an argument. Writing
  `python manage.py migrate --noinput && python manage.py ensure_admin ...`
  there fails with `manage.py migrate: error: unrecognized arguments`, and the
  container exits, taking the site down. Leave that field empty.
- **Pre-Deploy Command** shows a padlock: it is a paid feature and is not
  available on the free tier. Migrations therefore have to run at container
  start, not before deploy.

The image's `CMD` runs `docker-entrypoint.sh`, which does the right thing in the
right order:

1. `python manage.py migrate --noinput`
2. `python manage.py ensure_admin --with-demo`
3. `exec gunicorn ... --bind 0.0.0.0:$PORT`

Migrations belong at container start, not at image build. The old Dockerfile ran
`RUN python manage.py migrate --noinput || true` during the build, where there
is no database connection, so it either no-opped or failed silently behind the
`|| true` and nobody noticed until the site came back with no tables.

`ensure_admin` needs the tables to exist in order to give the superuser a
`Profile` row, which is why it cannot come before migrate.

If the dashboard's Docker Command field has been filled in, clear it.

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
