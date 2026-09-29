"""Tests for the demo accounts, the seed data and the admin user-create form.

Two production gaps are covered here:

* ``ensure_admin`` only ever created the single ``admin`` superuser, so the
  three-role demonstration (admin / staff / customer) had no second or third
  account to log in with, and ``music_genre`` / ``music_tag`` / ``music_songqueue``
  had zero rows, leaving the dashboard charts empty. ``--with-demo`` fills them
  in. The bare command must stay exactly as it was, because the Render start
  command (``python manage.py ensure_admin``) runs it on every deploy.
* ``user_create_view`` threw away the result of ``make_random_password()``, so
  every account an admin created was unusable. The create form now carries a
  real password pair.

The regression that these tests most exist to catch: ``create_user`` fires the
``post_save`` signal in ``music/models.py``, which already creates the
``Profile`` with the default ``role='customer'``. A plain ``get_or_create`` with
``defaults={'role': 'staff'}`` therefore finds the existing row and changes
nothing, leaving ``staff`` a customer.
"""

from io import StringIO

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from music.forms import UserCreateForm, UserForm
from music.models import Genre, Playlist, PlaylistSong, Profile, SongQueue, Tag

# The password the demonstration is run with. It is passed through the
# existing --password flag so the command never hardcodes a second secret.
DEMO_PASSWORD = "12345678"

THAI_RANGE = range(0x0E00, 0x0E80)


def has_thai(text):
    return any(ord(char) in THAI_RANGE for char in text)


class BareCommandTests(TestCase):
    """The no-flag path is what Render runs; demo data must never be default."""

    def test_creates_only_the_admin_user(self):
        call_command("ensure_admin", verbosity=0)

        self.assertTrue(User.objects.filter(username="admin").exists())
        self.assertFalse(User.objects.filter(username__in=["staff", "customer"]).exists())
        self.assertEqual(User.objects.count(), 1)

    def test_creates_no_catalogue_rows(self):
        call_command("ensure_admin", verbosity=0)

        self.assertEqual(Genre.objects.count(), 0)
        self.assertEqual(Tag.objects.count(), 0)
        self.assertEqual(SongQueue.objects.count(), 0)
        self.assertEqual(Playlist.objects.count(), 0)

    def test_does_not_mention_demo_data(self):
        out = StringIO()
        call_command("ensure_admin", stdout=out)

        self.assertNotIn("demo", out.getvalue().lower())


class DemoCommandTests(TestCase):
    """--with-demo must be complete enough to run the three-role demonstration."""

    @classmethod
    def setUpTestData(cls):
        call_command("ensure_admin", "--with-demo", password=DEMO_PASSWORD, verbosity=0)

    def test_creates_all_three_accounts_with_the_right_roles(self):
        expected = {"admin": "admin", "staff": "staff", "customer": "customer"}
        for username, role in expected.items():
            with self.subTest(username=username):
                user = User.objects.get(username=username)
                self.assertEqual(Profile.objects.get(user=user).role, role)

    def test_staff_is_a_staff_user_and_not_a_customer(self):
        # The post_save signal hands every new user a customer Profile, so a
        # get_or_create(defaults={"role": "staff"}) silently does nothing.
        staff = User.objects.get(username="staff")

        self.assertEqual(staff.profile.role, "staff")
        self.assertTrue(staff.profile.is_staff_role())
        self.assertFalse(staff.profile.can_manage_users())

    def test_customer_stays_a_customer_and_gains_no_extra_rights(self):
        customer = User.objects.get(username="customer")

        self.assertEqual(customer.profile.role, "customer")
        self.assertFalse(customer.is_staff)
        self.assertFalse(customer.is_superuser)
        self.assertFalse(customer.profile.is_staff_role())

    def test_every_demo_account_can_authenticate(self):
        for username in ("admin", "staff", "customer"):
            with self.subTest(username=username):
                self.assertIsNotNone(
                    authenticate(username=username, password=DEMO_PASSWORD)
                )

    def test_honours_the_password_flag(self):
        call_command("ensure_admin", "--with-demo", password="another-pass-77", verbosity=0)

        for username in ("admin", "staff", "customer"):
            with self.subTest(username=username):
                user = User.objects.get(username=username)
                self.assertTrue(user.check_password("another-pass-77"))

    def test_seeds_at_least_five_genres_and_five_tags(self):
        self.assertGreaterEqual(Genre.objects.count(), 5)
        self.assertGreaterEqual(Tag.objects.count(), 5)

    def test_seeded_genre_and_tag_names_keep_their_thai_characters(self):
        # Guards the Windows PowerShell encoding trap: a mangled write turns
        # these names into empty strings and every slug collides on unique.
        for genre in Genre.objects.all():
            with self.subTest(genre=genre.pk):
                self.assertTrue(has_thai(genre.name), genre.name)
                self.assertTrue(genre.slug)
        for tag in Tag.objects.all():
            with self.subTest(tag=tag.pk):
                self.assertTrue(has_thai(tag.name), tag.name)
                self.assertTrue(tag.slug)

    def test_seeds_at_least_ten_songs_with_playable_video_ids(self):
        self.assertGreaterEqual(SongQueue.objects.count(), 10)
        for song in SongQueue.objects.all():
            with self.subTest(song=song.pk):
                self.assertEqual(len(song.video_id), 11, song.video_id)

    def test_seed_has_both_played_and_queued_songs(self):
        self.assertTrue(SongQueue.objects.filter(is_played=True).exists())
        self.assertTrue(SongQueue.objects.filter(is_played=False).exists())

    def test_seed_has_a_thumbnail_so_the_queue_renders_an_image(self):
        self.assertTrue(SongQueue.objects.exclude(thumbnail="").exclude(thumbnail=None).exists())

    def test_songs_carry_genres_so_the_genre_chart_has_data(self):
        self.assertTrue(SongQueue.objects.filter(genres__isnull=False).exists())
        self.assertTrue(SongQueue.objects.filter(tags__isnull=False).exists())
        for genre in Genre.objects.all():
            with self.subTest(genre=genre.name):
                self.assertTrue(genre.queued_songs.exists(), genre.name)

    def test_seeds_a_playlist_owned_by_customer_with_reachable_songs(self):
        playlist = Playlist.objects.get(user__username="customer")

        entries = list(PlaylistSong.objects.filter(playlist=playlist))
        self.assertTrue(entries)
        self.assertTrue(all(entry.song_id is not None for entry in entries))
        self.assertEqual(
            [song.pk for song in playlist.get_songs_ordered()],
            [entry.song_id for entry in entries],
        )

    def test_prints_a_summary_with_the_credentials(self):
        # A second run creates nothing, so the summary has to report the totals
        # that are actually in the database, not only the rows it just made.
        out = StringIO()
        call_command("ensure_admin", "--with-demo", password=DEMO_PASSWORD, stdout=out)
        text = out.getvalue()

        for username in ("admin", "staff", "customer"):
            self.assertIn(username, text)
        self.assertIn(DEMO_PASSWORD, text)
        self.assertRegex(text, r"Genres\s*:\s*%d\b" % Genre.objects.count())
        self.assertRegex(text, r"Songs in queue\s*:\s*%d\b" % SongQueue.objects.count())
        self.assertRegex(text, r"Playlists\s*:\s*%d\b" % Playlist.objects.count())

    def test_running_twice_duplicates_nothing(self):
        def counts():
            return (
                User.objects.count(),
                Genre.objects.count(),
                Tag.objects.count(),
                SongQueue.objects.count(),
                Playlist.objects.count(),
                PlaylistSong.objects.count(),
            )

        before = counts()
        call_command("ensure_admin", "--with-demo", password=DEMO_PASSWORD, verbosity=0)
        after = counts()

        self.assertEqual(before, after)
        self.assertEqual(User.objects.count(), 3)


class UserCreateFormTests(TestCase):
    def _payload(self, **overrides):
        payload = {
            "username": "newwaiter",
            "first_name": "สมชาย",
            "last_name": "ใจดี",
            "email": "somchai@example.com",
            "is_active": "on",
            "password1": "Thongchai-99",
            "password2": "Thongchai-99",
        }
        payload.update(overrides)
        return payload

    def test_accepts_a_matching_password_pair(self):
        form = UserCreateForm(self._payload())

        self.assertTrue(form.is_valid(), form.errors)

    def test_rejects_a_mismatched_password_pair(self):
        form = UserCreateForm(self._payload(password2="Thongchai-98"))

        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)

    def test_rejects_a_password_django_considers_too_weak(self):
        # Django 6 reports password-strength errors on password2 (it validates
        # the confirmation field), so the property to pin is "rejected and shown
        # on a password field", not which of the two carries the message.
        with self.subTest(rule="minimum length"):
            form = UserCreateForm(self._payload(password1="ab1", password2="ab1"))
            self.assertFalse(form.is_valid())
            self.assertTrue({"password1", "password2"} & set(form.errors))

        with self.subTest(rule="similar to the username"):
            payload = self._payload(username="somchai123")
            payload["password1"] = payload["password2"] = "Somchai1234"
            form = UserCreateForm(payload)
            self.assertFalse(form.is_valid())
            self.assertTrue({"password1", "password2"} & set(form.errors))

    def test_carries_the_same_fields_the_edit_form_shows_plus_the_passwords(self):
        self.assertEqual(
            list(UserCreateForm().fields),
            ["username", "first_name", "last_name", "email", "is_active", "password1", "password2"],
        )

    def test_the_edit_form_is_left_without_password_fields(self):
        # user_edit_view saves UserForm on every profile edit; password fields
        # there would silently reset an existing user's password.
        self.assertNotIn("password1", UserForm().fields)
        self.assertNotIn("password2", UserForm().fields)


class UserCreateViewTests(TestCase):
    def setUp(self):
        # update_or_create + client.login, not create_user + force_login:
        # create_user's signal caches a role='customer' Profile on the user
        # object, and force_login then fires update_last_login -> post_save ->
        # save_user_profile, which re-saves that stale cached profile and
        # silently reverts the role. Same pattern as tests_nav.py.
        self.boss = User.objects.create_user("boss", password="Bosspass-42")
        Profile.objects.update_or_create(user=self.boss, defaults={"role": "admin"})
        self.client.login(username="boss", password="Bosspass-42")

    def _payload(self, **overrides):
        payload = {
            "username": "waiter1",
            "first_name": "ปกรณ์",
            "last_name": "แก้ว",
            "email": "waiter1@example.com",
            "is_active": "on",
            "password1": "Jukebox-77",
            "password2": "Jukebox-77",
            "role": "staff",
        }
        payload.update(overrides)
        return payload

    def test_created_user_can_immediately_use_the_submitted_password(self):
        response = self.client.post(reverse("user_create"), self._payload())

        self.assertRedirects(response, reverse("user_list"))
        user = User.objects.get(username="waiter1")
        self.assertTrue(user.check_password("Jukebox-77"))
        self.assertTrue(user.is_active)
        self.assertIsNotNone(authenticate(username="waiter1", password="Jukebox-77"))

    def test_created_user_gets_the_chosen_role(self):
        self.client.post(reverse("user_create"), self._payload(role="staff"))
        self.assertEqual(Profile.objects.get(user__username="waiter1").role, "staff")

        self.client.post(reverse("user_create"), self._payload(username="guest1", role="customer"))
        self.assertEqual(Profile.objects.get(user__username="guest1").role, "customer")

    def test_mismatched_passwords_do_not_create_a_user(self):
        self.client.post(reverse("user_create"), self._payload(password2="Jukebox-78"))

        self.assertFalse(User.objects.filter(username="waiter1").exists())

    def test_create_page_offers_the_password_fields(self):
        response = self.client.get(reverse("user_create"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "id_password1")
        self.assertContains(response, "id_password2")

    def test_edit_page_hides_the_password_fields(self):
        target = User.objects.create_user("editee", password="Keepme-123")
        response = self.client.get(reverse("user_edit", args=[target.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "id_password1")
        self.assertNotContains(response, "id_password2")

    def test_editing_a_user_does_not_touch_their_password(self):
        target = User.objects.create_user("editee", password="Keepme-123")

        self.client.post(
            reverse("user_edit", args=[target.pk]),
            {
                "username": "editee",
                "first_name": "แก้",
                "last_name": "ไข่",
                "email": "editee@example.com",
                "role": "staff",
            },
        )

        target.refresh_from_db()
        self.assertTrue(target.check_password("Keepme-123"))
        self.assertEqual(Profile.objects.get(user=target).role, "staff")
