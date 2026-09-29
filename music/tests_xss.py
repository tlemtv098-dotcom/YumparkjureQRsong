import json
import re

from django.test import TestCase

from music.models import ClientLog, SongQueue


def _const(html, name):
    """Return the JS literal the dashboard assigns to `name`, as written."""
    match = re.search(rf"const {name} = (.*?);", html, re.S)
    if match is None:
        raise AssertionError(f"{name} not found in rendered page")
    return match.group(1)


class _RateLimitResetMixin:
    """The endpoint throttler is a process-wide dict keyed on REMOTE_ADDR.

    Every test client here shares 127.0.0.1, so the counter has to be reset
    between tests or a slow run trips the production limit. Clearing the
    store is test-local: the production limit in views.py is untouched.
    """

    def setUp(self):
        from music.views import _rate_limit_store

        _rate_limit_store.clear()


class CleanTextUnitTests(TestCase):
    """The sanitiser's own contract, independent of any view."""

    def _clean(self, value, max_length=255):
        from music.views import _clean_text

        return _clean_text(value, max_length)

    def test_angle_brackets_are_removed_not_escaped(self):
        # Escaping would double up with the autoescaping Django already does
        # in templates and show users a literal "&lt;".
        self.assertEqual(self._clean("<b>hi</b>"), "bhi/b")
        self.assertNotIn("&lt;", self._clean("<script>"))

    def test_non_string_input_is_coerced(self):
        self.assertEqual(self._clean(1234), "1234")
        self.assertEqual(self._clean(None), "None")

    def test_whitespace_runs_collapse_and_edges_strip(self):
        self.assertEqual(self._clean("  a \t\n b  "), "a b")
        self.assertEqual(self._clean("   \t\n "), "")

    def test_truncates_to_max_length(self):
        self.assertEqual(self._clean("abcdefghij", 4), "abcd")


class QueueTitleSanitisationTests(_RateLimitResetMixin, TestCase):
    def _post(self, payload):
        return self.client.post(
            "/api/add/",
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_script_breakout_in_title_is_stripped(self):
        # The brief used "dQw4w9WgXcQ" here, but that id is in
        # views.BLOCKED_VIDEO_IDS, so /api/add/ answers 400 before it stores
        # anything. Any fresh 11-char id exercises the same path.
        response = self._post({
            "video_id": "xssVid00001",
            "title": "</script><img src=x onerror=alert(1)>",
            "client_id": "xss-title",
        })
        self.assertEqual(response.status_code, 200)
        song = SongQueue.objects.get(video_id="xssVid00001")
        self.assertNotIn("<", song.title)
        self.assertNotIn(">", song.title)
        self.assertNotIn("</script", song.title.lower())

    def test_clean_title_is_preserved_verbatim(self):
        response = self._post({
            "video_id": "aaaaaaaaaaa",
            "title": "BOWKYLION Ft. NONT TANONT - ที่คั่นหนังสือ",
            "client_id": "xss-clean",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            SongQueue.objects.get(video_id="aaaaaaaaaaa").title,
            "BOWKYLION Ft. NONT TANONT - ที่คั่นหนังสือ",
        )

    def test_channel_and_requested_by_are_stripped(self):
        self._post({
            "video_id": "bbbbbbbbbbb",
            "title": "ok",
            "channel": "<b>chan</b>",
            "requested_by": "<i>me</i>",
            "client_id": "xss-chan",
        })
        song = SongQueue.objects.get(video_id="bbbbbbbbbbb")
        self.assertNotIn("<", song.channel)
        self.assertNotIn(">", song.channel)
        self.assertNotIn("<", song.requested_by)
        self.assertNotIn(">", song.requested_by)

    def test_add_to_queue_front_is_also_sanitised(self):
        response = self.client.post(
            "/api/add-front/",
            data=json.dumps({
                "video_id": "ccccccccccc",
                "title": "<script>alert(1)</script>",
                "client_id": "xss-front",
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        title = SongQueue.objects.get(video_id="ccccccccccc").title
        self.assertNotIn("<", title)
        self.assertNotIn(">", title)

    def test_dashboard_json_cannot_break_out_of_the_script_block(self):
        from django.contrib.auth.models import User
        from django.urls import reverse
        from music.models import Profile

        self._post({
            "video_id": "ddddddddddd",
            "title": "</script><img src=x onerror=alert(1)>",
            "client_id": "xss-dash",
        })
        # views_auth.dashboard_view only puts is_played=True songs into
        # top_songs_json, so the payload has to be played before the page
        # would ever carry it.
        SongQueue.objects.filter(video_id="ddddddddddd").update(is_played=True)

        admin = User.objects.create_user(username="xss_admin", password="testpass123")
        Profile.objects.update_or_create(user=admin, defaults={"role": "admin"})
        self.client.login(username="xss_admin", password="testpass123")
        html = self.client.get(reverse("dashboard")).content.decode("utf-8")

        # The words "onerror=alert" still appear in the page: they are inert
        # text inside a JSON string, and a browser only acts on them when a
        # tag wraps them. The brief asserted their absence, which no
        # delimiter-removing sanitiser can deliver, so what is asserted here
        # is the property that actually stops execution -- the injected
        # literal cannot open a tag or close the script block.
        self.assertNotIn("</script><img", html)
        payload = _const(html, "topSongsData")
        self.assertNotIn("<", payload)
        self.assertNotIn(">", payload)
        parsed = json.loads(payload)
        self.assertEqual(parsed[0]["title"], "/scriptimg src=x onerror=alert(1)")


class ClientLogSanitisationTests(_RateLimitResetMixin, TestCase):
    def test_event_and_detail_are_stripped(self):
        self.client.post(
            "/api/clientlog/",
            data=json.dumps({
                "event": "<script>alert(1)</script>",
                "detail": "</script><img src=x onerror=alert(1)>",
            }),
            content_type="application/json",
        )
        log = ClientLog.objects.latest("id")
        self.assertNotIn("<", log.event)
        self.assertNotIn(">", log.event)
        self.assertNotIn("<", log.detail)
        self.assertNotIn(">", log.detail)
