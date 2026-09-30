"""CRUD coverage for the genre and tag management screens.

These views call ``GenreForm`` and ``TagForm``. Both names were missing from the
import list in ``music/views_auth.py``, so every create and edit POST raised
``NameError`` and returned a 500, while the list pages worked fine because they
never touch a form. The whole suite passed without noticing, because nothing
exercised the write path.

Every test here posts real form data, so a missing import cannot pass again.
Fixture names are deliberately ASCII: these tests verify that the view is wired
to a real form, not how Thai renders.
"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from music.models import Genre, Profile, Tag


class AdminCrudTestCase(TestCase):
    """Shared admin login."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username="crud_admin", password="testpass123"
        )
        Profile.objects.update_or_create(
            user=self.admin, defaults={"role": "admin"}
        )
        self.client.login(username="crud_admin", password="testpass123")


class GenreCrudTests(AdminCrudTestCase):
    def test_create_genre(self):
        response = self.client.post(
            reverse("genre_create"), {"name": "Luk Thung", "description": "fast"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Genre.objects.filter(name="Luk Thung").exists())

    def test_create_genre_rejects_duplicate_name(self):
        Genre.objects.create(name="Luk Thung")
        response = self.client.post(
            reverse("genre_create"), {"name": "Luk Thung", "description": ""}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Genre.objects.filter(name="Luk Thung").count(), 1)

    def test_edit_genre(self):
        genre = Genre.objects.create(name="Luk Thung")
        response = self.client.post(
            reverse("genre_edit", args=[genre.pk]),
            {"name": "String", "description": "changed"},
        )
        self.assertEqual(response.status_code, 302)
        genre.refresh_from_db()
        self.assertEqual(genre.name, "String")

    def test_delete_genre(self):
        genre = Genre.objects.create(name="Luk Thung")
        response = self.client.post(reverse("genre_delete", args=[genre.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Genre.objects.filter(pk=genre.pk).exists())

    def test_genre_list_renders(self):
        Genre.objects.create(name="Luk Thung")
        response = self.client.get(reverse("genre_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Luk Thung")

    def test_genre_create_page_renders(self):
        response = self.client.get(reverse("genre_create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form")


class TagCrudTests(AdminCrudTestCase):
    def test_create_tag(self):
        response = self.client.post(reverse("tag_create"), {"name": "Wedding"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Tag.objects.filter(name="Wedding").exists())

    def test_create_tag_rejects_duplicate_name(self):
        Tag.objects.create(name="Wedding")
        response = self.client.post(reverse("tag_create"), {"name": "Wedding"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Tag.objects.filter(name="Wedding").count(), 1)

    def test_edit_tag(self):
        tag = Tag.objects.create(name="Wedding")
        response = self.client.post(
            reverse("tag_edit", args=[tag.pk]), {"name": "Old Hit"}
        )
        self.assertEqual(response.status_code, 302)
        tag.refresh_from_db()
        self.assertEqual(tag.name, "Old Hit")

    def test_delete_tag(self):
        tag = Tag.objects.create(name="Wedding")
        response = self.client.post(reverse("tag_delete", args=[tag.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Tag.objects.filter(pk=tag.pk).exists())

    def test_tag_list_renders(self):
        Tag.objects.create(name="Wedding")
        response = self.client.get(reverse("tag_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Wedding")

    def test_tag_create_page_renders(self):
        response = self.client.get(reverse("tag_create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form")


class StaffWritePermissionTests(TestCase):
    """staff may write genres but must not reach user management."""

    def setUp(self):
        self.staff = User.objects.create_user(
            username="crud_staff", password="testpass123"
        )
        Profile.objects.update_or_create(
            user=self.staff, defaults={"role": "staff"}
        )
        self.client.login(username="crud_staff", password="testpass123")

    def test_staff_can_create_genre(self):
        response = self.client.post(
            reverse("genre_create"), {"name": "Rock", "description": ""}
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Genre.objects.filter(name="Rock").exists())

    def test_staff_cannot_open_user_management(self):
        response = self.client.get(reverse("user_list"))
        self.assertEqual(response.status_code, 302)
