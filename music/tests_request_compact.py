from django.test import TestCase

class RequestCompactTests(TestCase):
    def page(self):
        response = self.client.get("/request/")
        self.assertEqual(response.status_code, 200)
        return response.content.decode()

    def test_hit_list_caps_at_six(self):
        html = self.page()
        self.assertNotIn(".slice(0, 15)", html)
        self.assertIn(".slice(0, 6)", html)

    def test_search_results_cap_at_six(self):
        html = self.page()
        self.assertIn("searchResults.slice(0, 6).forEach", html)

    def test_single_my_songs_panel_sits_below_search(self):
        html = self.page()
        self.assertEqual(html.count('id="my-songs-list"'), 1)
        self.assertLess(html.index('id="my-songs-list"'), html.index('id="hit-list"'))

    def test_name_input_is_persisted(self):
        html = self.page()
        self.assertIn('id="requester-name"', html)
        self.assertIn("jukebox_requester_name", html)

    def test_my_songs_api_returns_requester_name(self):
        from music.models import SongQueue
        SongQueue.objects.create(
            title="t", video_id="abcdefghijk", requested_by="มิน",
            client_id="naming-case-1",
        )
        payload = self.client.get("/api/my-songs/", {"client_id": "naming-case-1"}).json()
        self.assertEqual(payload["songs"][0]["requested_by"], "มิน")

    def test_add_stores_custom_requester_name(self):
        from music.models import SongQueue
        self.client.post(
            "/api/add/", data={"title": "t2", "video_id": "abcdefghij1",
                                "requested_by": "มิน", "client_id": "naming-case-2"},
            content_type="application/json",
        )
        self.assertEqual(
            SongQueue.objects.get(video_id="abcdefghij1").requested_by, "มิน")

    def test_my_songs_rows_render_the_name(self):
        html = self.page()
        self.assertIn("song.requested_by", html)
