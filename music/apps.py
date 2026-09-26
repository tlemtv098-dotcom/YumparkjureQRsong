from django.apps import AppConfig


class MusicConfig(AppConfig):
    name = 'music'

    # The admin bootstrap deliberately does NOT live here any more. It used to
    # be a ready() method that queried the database, which is wrong twice over:
    #
    #   1. AppConfig.ready() runs at import time, before `migrate`, so the
    #      post_save signal that creates Profile fired while the music_profile
    #      table did not exist, and the bare `except` swallowed the error.
    #   2. Because the admin user had then been created anyway, no later boot
    #      called create_user again, so the signal never fired again and the
    #      missing Profile became permanent. The navbar keys off
    #      user.profile.role, so the superuser saw no admin links at all.
    #
    # It also made every management command emit
    # "RuntimeWarning: Accessing the database during app initialization".
    #
    # The bootstrap now lives in the `ensure_admin` management command, which is
    # safe to run after `migrate`:
    #
    #     python manage.py ensure_admin
