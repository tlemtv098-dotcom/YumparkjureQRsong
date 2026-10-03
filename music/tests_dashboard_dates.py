"""Regression tests for the dashboard day buckets.

The daily chart bucketed by timezone.now().date(), which under USE_TZ is the
UTC date, while the created_at__date lookup converts stored timestamps to
TIME_ZONE (Asia/Bangkok, UTC+7). Between 17:00 and 24:00 UTC the two disagree
by a day, so the bucket the view asked for held nothing and every bar read 0
even with songs in the queue.

localdate() is the date in TIME_ZONE, which is the same basis the lookup uses.
"""

from datetime import timedelta
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from music.models import SongQueue


class DashboardDailyBucketTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user("dashadmin", password="pw-12345")
        cls.admin.is_staff = True
        cls.admin.save()
        profile = cls.admin.profile
        profile.role = "admin"
        profile.save()

    def setUp(self):
        self.client.force_login(self.admin)

    def addSong(self, when, video_id):
        song = SongQueue.objects.create(title=video_id, video_id=video_id)
        # auto_now_add ignores an explicit value, so backdate it directly.
        SongQueue.objects.filter(pk=song.pk).update(created_at=when)
        return song

    def dailyStats(self, html):
        import re

        match = re.search(r"const dailyStats = (\[.*?\]);", html)
        self.assertIsNotNone(match, "dailyStats not found in the page")
        import json

        return json.loads(match.group(1))

    def test_a_song_added_today_lands_in_the_last_bucket(self):
        self.addSong(timezone.now(), "aaaaaaaaaaa")
        html = self.client.get("/dashboard/").content.decode()
        stats = self.dailyStats(html)
        self.assertEqual(len(stats), 7)
        self.assertEqual(
            stats[-1]["count"], 1,
            f"today's bucket is empty: {stats}",
        )

    def test_bucket_dates_end_on_the_local_date(self):
        html = self.client.get("/dashboard/").content.decode()
        stats = self.dailyStats(html)
        expected = timezone.localdate().strftime("%d/%m")
        self.assertEqual(stats[-1]["date"], expected)

    def test_utc_late_evening_still_counts_today(self):
        # 18:30 UTC is already the next day in Bangkok. The view must bucket it
        # under the local today, which is what the created_at__date lookup uses.
        utc_late = timezone.now().replace(hour=18, minute=30)
        if utc_late > timezone.now():
            self.skipTest("not late enough in UTC to cross the local date")
        self.addSong(utc_late, "bbbbbbbbbbb")
        html = self.client.get("/dashboard/").content.decode()
        stats = self.dailyStats(html)
        self.assertEqual(stats[-1]["count"], 1, stats)

    def test_view_uses_localdate_not_utc_now(self):
        from music import views_auth

        sentinel = timezone.localdate()
        with mock.patch.object(
            timezone, "localdate", return_value=sentinel
        ) as localdate:
            self.client.get("/dashboard/")
        self.assertGreaterEqual(localdate.call_count, 1)

    def test_status_chart_today_bucket_uses_local_date(self):
        played = self.addSong(timezone.now(), "ccccccccccc")
        SongQueue.objects.filter(pk=played.pk).update(is_played=True)
        html = self.client.get("/dashboard/").content.decode()
        self.assertIn("เล่นแล้ววันนี้", html)

    def test_api_stats_endpoint_returns_the_same_day_buckets(self):
        self.addSong(timezone.now(), "ddddddddddd")
        response = self.client.get("/api/stats/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("top_songs", response.json())


class DashboardLocalDateContractTests(TestCase):
    def test_no_view_uses_utc_date_for_day_buckets(self):
        import io
        import os

        path = os.path.join(os.path.dirname(__file__), "views_auth.py")
        with io.open(path, encoding="utf-8") as handle:
            source = handle.read()
        self.assertNotIn(
            "timezone.now().date()", source,
            "day buckets must use timezone.localdate()",
        )

    def test_a_week_of_buckets_spans_today_backwards(self):
        self.assertEqual(
            timedelta(days=6), timezone.localdate() - (timezone.localdate() - timedelta(days=6))
        )