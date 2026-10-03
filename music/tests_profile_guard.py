"""Regression tests for the profile view's missing-Profile guard.

Users created before migration 0008 have no Profile row, and the reverse
one-to-one accessor `request.user.profile` raises RelatedObjectDoesNotExist
for them, turning /accounts/profile/ into a 500. The view uses get_or_create
so the row is created on first visit instead.
"""

from django.contrib.auth.models import User
from django.test import TestCase

from music.models import Profile


class ProfileGuardTests(TestCase):
    def test_user_without_profile_row_gets_the_page(self):
        legacy = User.objects.create_user(username="legacy", password="testpass123")
        Profile.objects.filter(user=legacy).delete()
        self.client.login(username="legacy", password="testpass123")

        response = self.client.get("/accounts/profile/")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Profile.objects.filter(user=legacy).exists(),
            "the view did not create the missing Profile",
        )

    def test_existing_profile_is_not_duplicated(self):
        user = User.objects.create_user(username="hasprofile", password="testpass123")
        Profile.objects.update_or_create(
            user=user, defaults={"role": "staff", "phone": "0812345678"}
        )
        self.client.login(username="hasprofile", password="testpass123")

        self.client.get("/accounts/profile/")

        self.assertEqual(Profile.objects.filter(user=user).count(), 1)
        self.assertEqual(Profile.objects.get(user=user).phone, "0812345678")
        self.assertEqual(Profile.objects.get(user=user).role, "staff")

    def test_posting_to_the_form_saves_the_recreated_profile(self):
        legacy = User.objects.create_user(username="legacy_post", password="testpass123")
        Profile.objects.filter(user=legacy).delete()
        self.client.login(username="legacy_post", password="testpass123")

        response = self.client.post("/accounts/profile/", {"phone": "0899999999"})

        self.assertIn(response.status_code, (200, 302))
        self.assertEqual(Profile.objects.get(user=legacy).phone, "0899999999")

    def test_navigation_also_reaches_the_page_for_a_legacy_user(self):
        # The navbar links to /accounts/profile/, so a missing row would 500
        # from any page the user lands on.
        legacy = User.objects.create_user(username="legacy_nav", password="testpass123")
        Profile.objects.filter(user=legacy).delete()
        self.client.login(username="legacy_nav", password="testpass123")

        for url in ("/", "/accounts/profile/", "/dashboard/"):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_profile_view_does_not_use_the_reverse_accessor(self):
        import io
        import os

        path = os.path.join(os.path.dirname(__file__), "views_auth.py")
        with io.open(path, encoding="utf-8") as handle:
            source = handle.read()
        self.assertNotIn(
            "profile = request.user.profile",
            source,
            "the reverse accessor raises for users without a Profile row",
        )
        self.assertIn(
            "Profile.objects.get_or_create(user=request.user)", source
        )