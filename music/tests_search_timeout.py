"""Regression tests for the search timeouts.

The client cancelled the request after 8 seconds while a cold Render instance
needed about 55 seconds to answer, so every search aborted before a result
arrived and the panel stayed empty. The two sides now share a budget: the
server allows a realistic per-key timeout and the client waits long enough for
the whole key-rotation to finish.
"""

import io
import os
import re

from django.contrib.auth.models import User
from django.test import TestCase


CLIENT_ABORT_MS = 120_000
SERVER_TIMEOUT_S = 25


class SearchTimeoutTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user("timeoutadmin", password="pw-12345")
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

    def test_client_waits_long_enough(self):
        html = self.playerHtml()
        match = re.search(
            r"setTimeout\(\(\) => manualController\.abort\(\), (\d+)\)", html
        )
        self.assertIsNotNone(match, "the abort guard is gone")
        budget_ms = int(match.group(1))
        self.assertGreaterEqual(
            budget_ms, CLIENT_ABORT_MS,
            "the client still cancels before a cold instance can answer",
        )

    def test_client_budget_is_not_absurd(self):
        html = self.playerHtml()
        match = re.search(
            r"setTimeout\(\(\) => manualController\.abort\(\), (\d+)\)", html
        )
        self.assertLessEqual(int(match.group(1)), 180_000)

    def test_server_timeout_is_longer_than_the_old_eight_seconds(self):
        source = self.readViews()
        # Drop comments so a note mentioning "8s" cannot satisfy the search,
        # and so the regex only has to cope with the call itself.
        code = "\n".join(
            line for line in source.split("\n") if not line.strip().startswith("#")
        )
        match = re.search(
            r"youtube/v3/search\?\{params\}'?,\s*timeout=(\d+),", code
        )
        self.assertIsNotNone(match, "the search timeout is not found")
        self.assertGreaterEqual(int(match.group(1)), SERVER_TIMEOUT_S)

    def test_timeout_comment_records_the_reason(self):
        # Without the note the next person will "tidy" the number back to 8s.
        html = self.playerHtml()
        self.assertIn("aborted every search", html)

    @staticmethod
    def readViews():
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "music", "views.py",
        )
        with io.open(path, encoding="utf-8") as handle:
            return handle.read()

    def test_fallback_still_answers_when_quota_is_gone(self):
        from unittest import mock

        Songless = None
        with mock.patch("music.views.search_youtube", return_value=[]):
            payload = self.client.get("/api/search/", {"q": "ไม่มีในระบบ"}).json()
        self.assertEqual(payload["source"], "local")
        self.assertIsInstance(payload["results"], list)
        del Songless