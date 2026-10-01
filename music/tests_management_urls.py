"""The management templates must build their action URLs with {% url %}.

genre_list, tag_list and user_list all hardcoded /admin/... in their fetch
calls. Django serves its own admin at /admin/, so every delete and toggle
posted to the wrong place, got an HTML page back, and died on r.json() with
"Unexpected token '<'". Create and edit used {% url %} correctly, which is why
only the destructive half of every CRUD screen was broken and why a test suite
that builds URLs with reverse() never noticed: reverse() produces the correct
path, so it could not detect a template that never called it.

These tests read the rendered markup, which is the only place the hardcoded
string lived.
"""

import re

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from music.models import Genre, Profile, Tag


class ManagementActionUrlTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="url_admin", password="testpass123")
        Profile.objects.update_or_create(user=self.admin, defaults={"role": "admin"})
        self.client.login(username="url_admin", password="testpass123")
        Genre.objects.create(name="Rock")
        Tag.objects.create(name="Wedding")

    def _html(self, url_name):
        response = self.client.get(reverse(url_name))
        self.assertEqual(response.status_code, 200)
        return response.content.decode("utf-8")

    def test_no_template_posts_to_the_django_admin_prefix(self):
        for name in ("genre_list", "tag_list", "user_list"):
            with self.subTest(page=name):
                html = self._html(name)
                offenders = re.findall(r"fetch\(\s*[`'\"]/admin/[^`)]*", html)
                self.assertEqual(
                    offenders, [],
                    "%s posts to /admin/, which is Django's admin, not this app" % name,
                )

    def test_genre_delete_posts_to_the_management_route(self):
        html = self._html("genre_list")
        self.assertIn(reverse("genre_delete", args=[1]), html)

    def test_tag_delete_posts_to_the_management_route(self):
        html = self._html("tag_list")
        self.assertIn(reverse("tag_delete", args=[1]), html)

    def test_user_delete_and_toggle_post_to_the_management_routes(self):
        html = self._html("user_list")
        self.assertIn(reverse("user_delete", args=[self.admin.pk]), html)
        self.assertIn(reverse("user_toggle_active", args=[self.admin.pk]), html)

    def test_every_action_button_carries_a_management_path(self):
        for name, marker in (("genre_list", "deleteGenre"),
                             ("tag_list", "deleteTag"),
                             ("user_list", "deleteUser")):
            with self.subTest(page=name):
                html = self._html(name)
                calls = re.findall(r"onclick=\"%s\('([^']+)'\)" % marker, html)
                self.assertTrue(calls, "no %s button found" % marker)
                for url in calls:
                    self.assertTrue(
                        url.startswith("/management/"),
                        "%s button points at %s" % (marker, url),
                    )
