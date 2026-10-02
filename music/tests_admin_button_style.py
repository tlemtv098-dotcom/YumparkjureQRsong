"""Guard the outlined-button styling on the admin action cells.

The edit and delete controls used to be bare text with only a colour, so they
read as plain links rather than buttons. These tests pin the outlined look so
a later template edit does not quietly drop it back to unstyled text.
"""

from django.contrib.auth.models import User
from django.test import TestCase

from music.models import Genre, Tag

OUTLINE_TOKENS = ("px-3", "py-1.5", "rounded-lg", "border")


class AdminActionButtonStyleTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user("styleadmin", password="pw-12345")
        cls.admin.is_staff = True
        cls.admin.save()
        profile = cls.admin.profile
        profile.role = "admin"
        profile.save()

        # The action cell only renders for rows that exist, so every list
        # under test needs at least one row.
        cls.genre = Genre.objects.create(name="เพลงรัก")
        cls.tag = Tag.objects.create(name="ขวัญ")

    def setUp(self):
        self.client.force_login(self.admin)

    def actionHtml(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        return response.content.decode()

    def assertOutlined(self, html):
        # Check the classes sit on the same tag as the button text, so a
        # stray class elsewhere on the page cannot satisfy this.
        import re

        for label in ("แก้ไข", "ลบ"):
            pattern = (
                r'<(?:a|button)[^>]*class="([^"]*)"[^>]*>\s*' + label + r"\s*</"
            )
            match = re.search(pattern, html)
            self.assertIsNotNone(match, f"no <a>/<button> element labelled {label}")
            classes = match.group(1).split()
            for token in OUTLINE_TOKENS:
                self.assertIn(token, classes, f"{label} lost {token!r}: {classes}")

    def test_genre_list_actions_are_outlined_buttons(self):
        self.assertOutlined(self.actionHtml("/management/genres/"))

    def test_tag_list_actions_are_outlined_buttons(self):
        self.assertOutlined(self.actionHtml("/management/tags/"))

    def test_user_list_actions_are_outlined_buttons(self):
        self.assertOutlined(self.actionHtml("/management/users/"))

    def test_edit_button_uses_the_amber_outline(self):
        html = self.actionHtml("/management/genres/")
        self.assertIn("border-amber-300", html)
        self.assertIn("text-amber-700", html)

    def test_delete_button_uses_the_red_outline(self):
        html = self.actionHtml("/management/genres/")
        self.assertIn("border-red-300", html)
        self.assertIn("text-red-600", html)

    def test_active_toggle_button_is_amber_not_red(self):
        # A red toggle used to sit beside the red delete button, so the two
        # destructive-looking controls were indistinguishable.
        html = self.actionHtml("/management/users/")
        self.assertIn("border-yellow-300", html)
        self.assertNotIn("hover:underline", html)

    def test_inactive_toggle_button_is_green(self):
        user = User.objects.create_user("sleepy", password="pw-12345")
        user.is_active = False
        user.save()
        html = self.actionHtml("/management/users/")
        self.assertIn("border-green-300", html)

    def test_action_cell_wraps_buttons_in_a_flex_row(self):
        html = self.actionHtml("/management/genres/")
        self.assertIn('class="flex items-center justify-end gap-2"', html)