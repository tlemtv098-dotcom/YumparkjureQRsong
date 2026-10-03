"""Regression tests for the player search controls.

Two problems made the search look broken from the page:

1. The field had no submit button, so a search only fired if the visitor
   happened to press Enter or stop typing for 500 ms. Typing and waiting
   showed only the "เพลงแนะนำ" panel, which reads as "search returns nothing".
2. The Enter handler was bound to `keypress`, a deprecated event that Chrome
   does not deliver for every keypress, so Enter could silently do nothing.

These tests pin the button and the keydown binding.
"""

import re

from django.contrib.auth.models import User
from django.test import TestCase

from music.models import Profile


class PlayerSearchControlsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user("searchadmin", password="pw-12345")
        cls.admin.is_staff = True
        cls.admin.save()
        profile = cls.admin.profile
        profile.role = "admin"
        profile.save()

    def setUp(self):
        self.client.force_login(self.admin)

    def playerHtml(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        return response.content.decode()

    def test_search_field_is_present(self):
        self.assertIn('id="manual-search"', self.playerHtml())

    def test_a_visible_search_button_exists(self):
        html = self.playerHtml()
        match = re.search(r"<button[^>]*id=\"manual-search-btn\"[^>]*>", html)
        self.assertIsNotNone(match, "no search button rendered")
        button = match.group(0)
        # It has to be a real button, not a hidden helper element.
        self.assertIn("<button", html[match.start():match.start() + 8])
        self.assertNotIn("hidden", button)
        self.assertIn("manualSearch()", button, "button is not wired to the search")
        self.assertIn("aria-label", button)

    def test_button_sits_next_to_the_input_in_a_flex_row(self):
        html = self.playerHtml()
        match = re.search(
            r'class="relative flex gap-2"', html)
        self.assertIsNotNone(match, "search row is not a flex container")
        self.assertLess(html.index('id="manual-search"'), html.index('id="manual-search-btn"'))

    def test_input_keeps_flexible_width(self):
        # The input used to be w-full, which would push the button outside the
        # panel once the row became a flex container.
        html = self.playerHtml()
        tag = re.search(r"<input[^>]*id=\"manual-search\"[^>]*>", html, re.S).group(0)
        self.assertNotIn("w-full", tag)
        self.assertIn("flex-1", tag)
        self.assertIn("min-w-0", tag)

    def test_enter_is_bound_with_keydown(self):
        html = self.playerHtml()
        self.assertIn('addEventListener("keydown"', html)
        self.assertNotIn(
            'addEventListener("keypress"', html,
            "keypress is deprecated and drops Enter in Chrome",
        )

    def test_enter_handler_prevents_default_and_searches(self):
        html = self.playerHtml()
        match = re.search(
            r'addEventListener\("keydown".*?\}\);', html, re.S)
        self.assertIsNotNone(match)
        handler = match.group(0)
        self.assertIn('e.key === "Enter"', handler)
        self.assertIn("preventDefault", handler)
        self.assertIn("manualSearch()", handler)

    def test_search_api_returns_a_list_shape(self):
        # Not asserting results are non-empty: search_youtube() calls the
        # YouTube Data API and fast-fails to [] when no key is configured, so
        # a result count here would test the environment, not this code. The
        # live site supplies a key and does return songs.
        response = self.client.get("/api/search/", {"q": "love"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("results", payload)
        self.assertIsInstance(payload["results"], list)

    def test_thai_query_is_accepted(self):
        response = self.client.get("/api/search/", {"q": "รัก"})
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json()["results"], list)

    def test_empty_query_is_handled(self):
        response = self.client.get("/api/search/", {"q": ""})
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json()["results"], list)

    def test_results_container_is_rendered(self):
        self.assertIn('id="manual-results"', self.playerHtml())