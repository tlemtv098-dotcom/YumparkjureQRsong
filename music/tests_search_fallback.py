"""Tests for the search fallback when the YouTube quota is spent.

search_youtube() fast-fails to [] when no key is configured or the daily quota
is gone, which left the search panel empty with no explanation. search_song now
falls back to songs already in the database, which costs no quota at all, and
reports which source answered so the client can tell the two apart.
"""

from django.contrib.auth.models import User
from django.test import TestCase
from unittest import mock

from music.models import SongQueue
from music.views import search_song, _local_song_search


class LocalSongSearchTests(TestCase):
    def setUp(self):
        self.song = SongQueue.objects.create(
            title="คำยินดี - Klear",
            video_id="aaaaaaaaaaa",
            channel="Genierock",
            thumbnail="https://example.test/a.jpg",
        )

    def test_finds_a_stored_song(self):
        found = _local_song_search("คำยินดี")
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["id"], "aaaaaaaaaaa")
        self.assertEqual(found[0]["title"], "คำยินดี - Klear")

    def test_shape_matches_the_youtube_payload(self):
        found = _local_song_search("คำยินดี")[0]
        # The player reads exactly these four keys.
        self.assertEqual(sorted(found), ["channel", "id", "thumbnail", "title"])

    def test_search_is_case_insensitive(self):
        SongQueue.objects.create(title="Love Song", video_id="bbbbbbbbbbb")
        self.assertEqual(len(_local_song_search("love song")), 1)

    def test_no_match_returns_empty(self):
        self.assertEqual(_local_song_search("ไม่มีเพลงนี้แน่นอน"), [])

    def test_duplicate_titles_are_collapsed(self):
        SongQueue.objects.create(title="คำยินดี - อีกเวอร์ชัน", video_id="aaaaaaaaaaa")
        found = _local_song_search("คำยินดี")
        self.assertEqual(len(found), 1)

    def test_blocked_video_is_skipped(self):
        from music.views import BLOCKED_VIDEO_IDS

        blocked_id = next(iter(BLOCKED_VIDEO_IDS))
        SongQueue.objects.create(title="เพลงต้องห้าม", video_id=blocked_id)
        found = _local_song_search("เพลงต้องห้าม")
        self.assertEqual(found, [])

    def test_limit_is_respected(self):
        for i in range(8):
            SongQueue.objects.create(
                title=f"เพลงสำรอง {i}", video_id=f"ccccccccccc"[0:10] + str(i % 10)
            )
        self.assertLessEqual(len(_local_song_search("เพลงสำรอง", limit=3)), 3)


class SearchSongFallbackTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user("searchadmin", password="pw-12345")
        cls.admin.is_staff = True
        cls.admin.save()
        profile = cls.admin.profile
        profile.role = "admin"
        profile.save()
        SongQueue.objects.create(
            title="คำยินดี - Klear", video_id="aaaaaaaaaaa", channel="Genierock"
        )

    def setUp(self):
        self.client.force_login(self.admin)

    def test_empty_query_returns_nothing(self):
        response = self.client.get("/api/search/", {"q": ""})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"], [])

    def test_youtube_result_is_reported_as_youtube(self):
        with mock.patch(
            "music.views.search_youtube",
            return_value=[{
                "id": "zzzzzzzzzzz", "title": "คำยินดี สด",
                "channel": "Official", "thumbnail": "",
            }],
        ):
            payload = self.client.get("/api/search/", {"q": "คำยินดี"}).json()
        self.assertEqual(payload["source"], "youtube")
        self.assertEqual(payload["results"][0]["id"], "zzzzzzzzzzz")

    def test_quota_exhaustion_falls_back_to_stored_songs(self):
        with mock.patch("music.views.search_youtube", return_value=[]):
            payload = self.client.get("/api/search/", {"q": "คำยินดี"}).json()
        self.assertEqual(payload["source"], "local")
        self.assertEqual(len(payload["results"]), 1)
        self.assertEqual(payload["results"][0]["id"], "aaaaaaaaaaa")

    def test_fallback_still_returns_the_documented_shape(self):
        with mock.patch("music.views.search_youtube", return_value=[]):
            payload = self.client.get("/api/search/", {"q": "คำยินดี"}).json()
        self.assertEqual(
            sorted(payload["results"][0]), ["channel", "id", "thumbnail", "title"]
        )

    def test_source_key_is_always_present(self):
        for youtube in ([{
            "id": "zzzzzzzzzzz", "title": "t", "channel": "c", "thumbnail": "",
        }], []):
            with mock.patch("music.views.search_youtube", return_value=youtube):
                payload = self.client.get("/api/search/", {"q": "คำยินดี"}).json()
            self.assertIn(payload["source"], ("youtube", "local"))

    def test_fallback_consumes_no_quota(self):
        # The fallback path must never reach the YouTube API again.
        with mock.patch("music.views.youtube_api_search") as api:
            with mock.patch("music.views.search_youtube", return_value=[]):
                self.client.get("/api/search/", {"q": "คำยินดี"})
        api.assert_not_called()

    def test_filtered_out_youtube_results_trigger_the_fallback(self):
        from music.views import BLOCKED_VIDEO_IDS

        blocked_id = next(iter(BLOCKED_VIDEO_IDS))
        with mock.patch(
            "music.views.search_youtube",
            return_value=[{
                "id": blocked_id, "title": "t", "channel": "c", "thumbnail": "",
            }],
        ):
            payload = self.client.get("/api/search/", {"q": "คำยินดี"}).json()
        self.assertEqual(payload["source"], "local")