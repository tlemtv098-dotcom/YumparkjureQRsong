"""Authorisation tests for the block endpoint.

block_video was the only endpoint in the owner-gated family - mark_played,
move_queue, unblock_video, clear_blocked - with no _is_owner check. Any
anonymous caller could POST an id and permanently remove that song from the
shop: add_to_queue rejects a blocked video_id, so it was a denial of service on
the catalogue rather than a cosmetic leak.
"""

from django.conf import settings
from django.test import TestCase

from music.models import BlockedVideo

TOKEN = {"HTTP_X_PLAYER_TOKEN": settings.PLAYER_TOKEN}


class BlockAuthorisationTests(TestCase):
    def test_anonymous_cannot_block(self):
        response = self.client.post("/api/block/aaaaaaaaaaa/")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(BlockedVideo.objects.count(), 0)

    def test_anonymous_cannot_block_a_fallback_id(self):
        """Even the early skip path must not be reachable anonymously."""
        response = self.client.post("/api/block/ks7p6DA0dKk/")
        self.assertEqual(response.status_code, 403)

    def test_owner_can_block(self):
        response = self.client.post("/api/block/aaaaaaaaaaa/", **TOKEN)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "blocked")
        self.assertTrue(BlockedVideo.objects.filter(video_id="aaaaaaaaaaa").exists())

    def test_owner_blocking_is_idempotent(self):
        self.client.post("/api/block/aaaaaaaaaaa/", **TOKEN)
        self.client.post("/api/block/aaaaaaaaaaa/", **TOKEN)
        self.assertEqual(BlockedVideo.objects.filter(video_id="aaaaaaaaaaa").count(), 1)

    def test_django_is_staff_session_can_block(self):
        """_is_owner accepts the player token OR an authenticated is_staff session."""
        from django.contrib.auth.models import User
        from music.models import Profile
        user = User.objects.create_user(username="block_staff", password="testpass123")
        Profile.objects.update_or_create(user=user, defaults={"role": "staff"})
        user.is_staff = True
        user.save()
        self.client.login(username="block_staff", password="testpass123")
        response = self.client.post("/api/block/bbbbbbbbbbb/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(BlockedVideo.objects.filter(video_id="bbbbbbbbbbb").exists())

    def test_profile_role_staff_without_is_staff_is_not_an_api_owner(self):
        """Documents the seam between the two notions of staff.

        _is_owner keys off User.is_staff, not Profile.role. A user created
        through the admin user-management screen gets Profile.role='staff' and
        full access to the management pages, but not owner rights on these APIs,
        which are reserved for the player token or a Django is_staff session.
        Recorded so the boundary is explicit rather than a surprise.
        """
        from django.contrib.auth.models import User
        from music.models import Profile
        user = User.objects.create_user(username="role_only", password="testpass123")
        Profile.objects.update_or_create(user=user, defaults={"role": "staff"})
        self.client.login(username="role_only", password="testpass123")
        response = self.client.post("/api/block/ddddddddddd/")
        self.assertEqual(response.status_code, 403)
        self.assertFalse(BlockedVideo.objects.filter(video_id="ddddddddddd").exists())

    def test_get_is_not_allowed(self):
        response = self.client.get("/api/block/aaaaaaaaaaa/", **TOKEN)
        self.assertEqual(response.status_code, 405)

    def test_blocked_video_cannot_be_added_to_the_queue(self):
        """The impact that made the missing gate serious."""
        import json
        BlockedVideo.objects.create(video_id="ccccccccccc", reason="Error 153")
        response = self.client.post(
            "/api/add/",
            data=json.dumps({"video_id": "ccccccccccc", "title": "x", "client_id": "p"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["status"], "failed")
