"""The queue API must hand the client a usable artwork URL.

SongQueue.artwork is an ImageField. get_queue serialised it with .values(),
which returns the raw storage path such as "artwork/ab12.jpg" rather than a
URL. No <img> can load that, so every client silently fell back to the YouTube
thumbnail and an uploaded cover was never displayed anywhere in the system.
"""

import io

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.test import TestCase
from django.urls import reverse

from music.models import Profile, SongQueue


def _png_bytes():
    """A minimal valid PNG, built without touching the filesystem."""
    import base64
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmM"
        "IQAAAABJRU5ErkJggg=="
    )


class QueueArtworkUrlTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="art_admin", password="testpass123")
        Profile.objects.update_or_create(user=self.admin, defaults={"role": "admin"})
        self.client.login(username="art_admin", password="testpass123")

    def _add(self, video_id, with_art):
        song = SongQueue.objects.create(
            title="Song " + video_id, video_id=video_id, is_played=False
        )
        if with_art:
            song.artwork.save(video_id + ".png", ContentFile(_png_bytes()), save=True)
        return song

    def _first(self):
        response = self.client.get("/api/queue/?page=1&per_page=50")
        self.assertEqual(response.status_code, 200)
        return response.json()["queue"][0]

    def test_artwork_is_a_resolvable_url_when_present(self):
        self._add("aaaaaaaaaaa", with_art=True)
        artwork = self._first()["artwork"]
        self.assertTrue(artwork.startswith("/media/artwork/"), artwork)
        self.assertTrue(artwork.endswith(".png"), artwork)

    def test_artwork_url_actually_serves_the_image(self):
        song = self._add("bbbbbbbbbbb", with_art=True)
        artwork = self._first()["artwork"]
        self.assertEqual(self.client.get(artwork).status_code, 200)

    def test_artwork_is_empty_string_when_unset(self):
        self._add("ccccccccccc", with_art=False)
        self.assertEqual(self._first()["artwork"], "")

    def test_payload_keeps_the_other_fields(self):
        self._add("ddddddddddd", with_art=False)
        row = self._first()
        for key in ("id", "title", "video_id", "thumbnail", "channel",
                    "requested_by", "audio_url", "artwork"):
            self.assertIn(key, row)

    def test_player_prefers_artwork_over_thumbnail(self):
        """The lock-screen metadata must fall back to artwork, not only thumbnail."""
        html = io.open(
            "music/templates/music/player.html", encoding="utf-8", newline=""
        ).read()
        self.assertIn("currentSong.artwork||currentSong.thumbnail", html)
        self.assertNotIn("artwork: [{src: currentSong.thumbnail", html)
