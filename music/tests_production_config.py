"""Regression tests for the production configuration fixes.

Two defects were found on the live Render deployment:

* the parsed ``DATABASE_URL`` forced ``sslmode=require``, which makes Render's
  own *internal* Postgres impossible to connect to, and
* the ``admin`` superuser could end up with no ``Profile`` row at all, which
  silently hides the user-management, genre and tag links in the navbar even
  though the user is a superuser.
"""

import importlib.util
import os
import warnings
from io import StringIO
from pathlib import Path
from unittest import mock

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase

from music.models import Profile

SETTINGS_PATH = Path(__file__).resolve().parent.parent / "yum_jukebox" / "settings.py"

# Keys the settings module reads from the environment. They are cleared before
# each probe load so a developer's own shell/.env cannot influence the result.
_ENV_KEYS = ("DATABASE_URL", "DATABASE_SSL_REQUIRE", "SECRET_KEY", "DEBUG")

POSTGRES_URL = "postgresql://jukebox:secret@db.example.com:5432/jukebox"


def load_settings(**env):
    """Import a throwaway copy of ``yum_jukebox/settings.py`` under a private name.

    A separate module object is deliberate: reloading the real
    ``yum_jukebox.settings`` module would repoint ``django.conf.settings`` at
    whatever ``DATABASE_URL`` the test just injected and corrupt the running
    test process.

    Returns ``(module, warning_messages)``.
    """
    spec = importlib.util.spec_from_file_location(
        "yum_jukebox_settings_probe", SETTINGS_PATH
    )
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(os.environ, env, clear=False):
        for key in _ENV_KEYS:
            if key not in env:
                os.environ.pop(key, None)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            spec.loader.exec_module(module)
    return module, [str(w.message) for w in caught]


class EnsureAdminCommandTests(TestCase):
    def test_creates_admin_with_profile(self):
        call_command("ensure_admin", verbosity=0)
        admin = User.objects.get(username="admin")
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.check_password("11111111"))
        self.assertEqual(Profile.objects.get(user=admin).role, "admin")

    def test_is_idempotent(self):
        call_command("ensure_admin", verbosity=0)
        call_command("ensure_admin", verbosity=0)
        self.assertEqual(User.objects.filter(username="admin").count(), 1)
        self.assertEqual(Profile.objects.filter(user__username="admin").count(), 1)

    def test_repairs_an_admin_that_has_no_profile(self):
        # The live bug: ready() created the superuser before `migrate` ran, the
        # post_save signal could not write music_profile, the error was swallowed,
        # and from then on the user already existed so the signal never fired again.
        admin = User.objects.create_user("admin", password="stale")
        Profile.objects.filter(user=admin).delete()
        self.assertFalse(Profile.objects.filter(user=admin).exists())

        call_command("ensure_admin", verbosity=0)

        admin = User.objects.get(username="admin")
        self.assertTrue(admin.check_password("11111111"))
        self.assertEqual(Profile.objects.get(user=admin).role, "admin")

    def test_custom_password_is_honoured(self):
        call_command("ensure_admin", password="other-pass-9", verbosity=0)
        self.assertTrue(User.objects.get(username="admin").check_password("other-pass-9"))

    def test_promotes_an_existing_non_superuser(self):
        User.objects.create_user("admin", password="11111111")
        call_command("ensure_admin", verbosity=0)
        admin = User.objects.get(username="admin")
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertEqual(Profile.objects.get(user=admin).role, "admin")

    def test_repairs_a_profile_left_with_the_default_role(self):
        # create_superuser fires the post_save signal, which creates Profile with
        # the default role 'customer'. The navbar keys off that role, so this
        # state hides the admin links just as badly as a missing row does.
        admin = User.objects.create_superuser("admin", password="11111111")
        self.assertEqual(Profile.objects.get(user=admin).role, "customer")

        call_command("ensure_admin", verbosity=0)

        self.assertEqual(Profile.objects.get(user=admin).role, "admin")

    def test_reports_every_action_and_a_summary(self):
        out = StringIO()
        call_command("ensure_admin", stdout=out)
        first = out.getvalue()
        # Two actions (superuser, Profile role) plus one summary line.
        self.assertEqual(len(first.strip().splitlines()), 3)
        self.assertIn("superuser", first)
        self.assertIn("Profile", first)
        self.assertIn("2 action(s)", first)

        out = StringIO()
        call_command("ensure_admin", stdout=out)
        second = out.getvalue()
        # Nothing left to do: the summary line only.
        self.assertEqual(len(second.strip().splitlines()), 1)
        self.assertIn("0 action(s)", second)


class DatabaseSslSettingTests(SimpleTestCase):
    def test_ssl_is_not_forced_when_env_var_is_absent(self):
        module, _ = load_settings(DATABASE_URL=POSTGRES_URL)
        self.assertNotIn("sslmode", module.DATABASES["default"].get("OPTIONS", {}))

    def test_sslmode_already_in_the_url_is_kept(self):
        module, _ = load_settings(DATABASE_URL=POSTGRES_URL + "?sslmode=require")
        self.assertEqual(
            module.DATABASES["default"]["OPTIONS"]["sslmode"], "require"
        )

    def test_database_ssl_require_env_var_turns_ssl_on(self):
        for value in ("1", "true", "YES"):
            with self.subTest(value=value):
                module, _ = load_settings(
                    DATABASE_URL=POSTGRES_URL, DATABASE_SSL_REQUIRE=value
                )
                self.assertEqual(
                    module.DATABASES["default"]["OPTIONS"]["sslmode"], "require"
                )

    def test_conn_max_age_is_preserved(self):
        module, _ = load_settings(DATABASE_URL=POSTGRES_URL)
        self.assertEqual(module.DATABASES["default"]["CONN_MAX_AGE"], 600)

    def test_falls_back_to_sqlite_without_database_url(self):
        module, _ = load_settings()
        self.assertEqual(
            module.DATABASES["default"]["ENGINE"], "django.db.backends.sqlite3"
        )


class SecretKeyWarningTests(SimpleTestCase):
    def _secret_key_warnings(self, **env):
        _, caught = load_settings(**env)
        return [message for message in caught if "SECRET_KEY" in message]

    def test_warns_loudly_when_secret_key_is_missing_in_production(self):
        self.assertTrue(self._secret_key_warnings(DEBUG="False"))

    def test_silent_when_secret_key_is_provided(self):
        self.assertEqual(self._secret_key_warnings(DEBUG="False", SECRET_KEY="k" * 60), [])

    def test_silent_while_debug_is_on(self):
        self.assertEqual(self._secret_key_warnings(), [])
