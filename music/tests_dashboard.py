import json
import re

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from music.models import Genre, Profile, SongQueue


class DashboardChartTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="dash_admin", password="testpass123")
        Profile.objects.update_or_create(user=self.user, defaults={"role": "admin"})
        self.client.login(username="dash_admin", password="testpass123")
        genre = Genre.objects.create(name="ผัดเพลง")
        for i in range(3):
            # SongQueue has no `genre` field -- genres is a M2M, so it must be
            # attached after creation, not passed to create().
            song = SongQueue.objects.create(
                title=f"เพลงที่ {i}", video_id=f"abcdefghij{i}", is_played=True,
            )
            song.genres.add(genre)

    def _const(self, html, name):
        match = re.search(rf"const {name} = (.*?);", html, re.S)
        self.assertIsNotNone(match, f"{name} not found in rendered page")
        return match.group(1)

    def test_dashboard_never_renders_a_raw_queryset(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "<QuerySet")

    def test_every_chart_payload_is_valid_json(self):
        html = self.client.get(reverse("dashboard")).content.decode("utf-8")
        # Every key the Chart.js code reads, per payload. Without this, a
        # regression renaming e.g. "date" to "dt" still parses as JSON and
        # renders `undefined` axis labels.
        for const, keys in (
            ("genreData", ("name", "song_count")),
            ("dailyStats", ("date", "count")),
            ("topSongsData", ("title", "play_count")),
            ("statusData", ("status", "count")),
        ):
            with self.subTest(chart=const):
                payload = json.loads(self._const(html, const))
                self.assertIsInstance(payload, list)
                self.assertTrue(payload, f"{const} is empty despite seeded data")
                for key in keys:
                    self.assertIn(key, payload[0], f"{const} is missing chart key {key!r}")

    def test_genre_chart_contains_real_data(self):
        html = self.client.get(reverse("dashboard")).content.decode("utf-8")
        payload = json.loads(self._const(html, "genreData"))
        self.assertEqual(payload[0]["name"], "ผัดเพลง")
        self.assertEqual(payload[0]["song_count"], 3)

    def test_thai_text_is_not_escaped_in_the_script(self):
        html = self.client.get(reverse("dashboard")).content.decode("utf-8")
        # One assertion per Thai-bearing payload: json.loads accepts \uXXXX
        # escapes, so each ensure_ascii=False is pinned independently.
        # daily_stats_json holds "%d/%m" digits only, so there is no Thai to
        # pin there and ensure_ascii is not observable for that payload.
        self.assertIn("ผัดเพลง", self._const(html, "genreData"))
        self.assertIn("เพลงที่ 0", self._const(html, "topSongsData"))
        self.assertIn("รอเล่น", self._const(html, "statusData"))

    def test_stats_api_rejects_non_numeric_period(self):
        response = self.client.get(reverse("dashboard_stats_api"), {"period": "abc"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["daily_stats"]), 7)

    def test_stats_api_response_keys_are_unchanged(self):
        payload = self.client.get(reverse("dashboard_stats_api")).json()
        self.assertEqual(set(payload), {"daily_stats", "top_songs", "status_stats"})
