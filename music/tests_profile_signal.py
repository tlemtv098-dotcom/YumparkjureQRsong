"""Tests for the post_save receiver in music/models.py.

The bug this file exists to pin: `music/models.py` used to carry a second
post_save receiver, `save_user_profile`, that re-saved `instance.profile` on
every User save. Django caches a reverse one-to-one on the instance the first
time it is read, and `Profile.objects.create(user=instance)` inside the
creation receiver populates that cache with a role='customer' copy. Any later
User save -- `update_last_login` on login is the one that happens in
production -- then wrote that stale copy back over whatever role application
code had just set.

So a promoted staff member silently became a customer again, which is fatal
for a role-based access control demonstration. These tests cover both halves:
new users must still get a Profile automatically, and an existing role must
survive a User save.
"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from music.models import Profile

PASSWORD = "Jukebox-77"


def promote(user, role):
    """Set a role the way application code does: through a fresh Profile query.

    The admin views fetch the Profile row, change it and save it, so the copy
    cached on the User instance by the creation signal is left behind
    untouched -- which is exactly the stale copy the write-back used to
    resurrect.
    """
    profile = Profile.objects.get(user=user)
    profile.role = role
    profile.save()
    return profile


class ProfileCreationTests(TestCase):
    def test_a_new_user_gets_a_profile_automatically(self):
        # register_view and ensure_admin both rely on this happening with no
        # explicit Profile.objects.create() call of their own.
        user = User.objects.create_user("newcomer", password=PASSWORD)

        self.assertTrue(Profile.objects.filter(user=user).exists())
        self.assertEqual(Profile.objects.get(user=user).role, "customer")


class RoleSurvivesUserSaveTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("promoted", password=PASSWORD)

    def test_saving_the_user_leaves_the_role_the_application_set(self):
        # The regression test. create_user cached a role='customer' Profile on
        # self.user; promote() then wrote role='staff' through a different
        # instance. self.user.save() must not undo that.
        promote(self.user, "staff")
        self.assertEqual(Profile.objects.get(user=self.user).role, "staff")

        self.user.save()

        self.assertEqual(
            Profile.objects.get(user=self.user).role,
            "staff",
            "saving the User reverted the role, the Profile signal is writing a "
            "stale cached Profile back",
        )

    def test_role_survives_force_login(self):
        # force_login fires the same user_logged_in signal as a real login, so
        # it also triggers update_last_login -> User.save().
        promote(self.user, "admin")

        self.client.force_login(self.user)

        self.assertEqual(Profile.objects.get(user=self.user).role, "admin")

    def test_role_survives_a_real_login(self):
        promote(self.user, "staff")

        self.assertTrue(self.client.login(username="promoted", password=PASSWORD))

        self.assertEqual(Profile.objects.get(user=self.user).role, "staff")


class RegisterViewRoleTests(TestCase):
    def _payload(self, **overrides):
        payload = {
            "username": "walkin",
            "first_name": "สมชาย",
            "last_name": "ใจดี",
            "email": "walkin@example.com",
            "phone": "0812345678",
            "password1": PASSWORD,
            "password2": PASSWORD,
        }
        payload.update(overrides)
        return payload

    def test_registration_leaves_the_new_user_a_customer(self):
        # The security property: whatever is posted, a self-registered account
        # must come out as role='customer', never admin or staff.
        self.client.post(reverse("register"), self._payload(role="admin"))

        self.assertTrue(User.objects.filter(username="walkin").exists())
        self.assertEqual(
            Profile.objects.get(user__username="walkin").role,
            "customer",
        )

    def test_registration_creates_the_profile_through_the_view(self):
        self.client.post(reverse("register"), self._payload())

        user = User.objects.get(username="walkin")
        self.assertEqual(user.profile.phone, "0812345678")
        self.assertFalse(user.profile.is_staff_role())
        self.assertFalse(user.profile.can_manage_users())
