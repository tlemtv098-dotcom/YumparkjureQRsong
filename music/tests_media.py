import os
import shutil
import tempfile
from pathlib import Path
from unittest import skipUnless

from django.test import TestCase

# One level above the per-run MEDIA_ROOT, so "../<name>" resolves to a file that
# really exists. The other traversal test targets a path that does not exist on
# disk, so it would pass even with no guard at all; this one fails loudly without
# the guard.
CANARY_NAME = "mysong_media_canary.txt"
CANARY_BYTES = b"mysong-media-canary-9d1f-secret"


class MediaServingTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # A private directory per run: no fixed shared path, nothing left behind
        # afterwards, and no chance of another user pre-creating the files we
        # write below.
        cls.work_dir = Path(tempfile.mkdtemp(prefix="mysong_media_test_"))
        cls.media_root = cls.work_dir / "media"
        cls.media_root.mkdir()
        (cls.media_root / "probe.txt").write_text("ok", encoding="utf-8")
        (cls.media_root / "avatar.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        (cls.work_dir / CANARY_NAME).write_bytes(CANARY_BYTES)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.work_dir, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        # MEDIA_ROOT is only known per run, so it cannot be a class decorator.
        self.media_override = self.settings(MEDIA_ROOT=self.media_root)
        self.media_override.enable()

    def tearDown(self):
        self.media_override.disable()
        super().tearDown()

    def test_media_file_is_served(self):
        response = self.client.get("/media/probe.txt")
        self.assertEqual(response.status_code, 200)

    def test_binary_media_file_is_served_intact(self):
        response = self.client.get("/media/avatar.png")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), b"\x89PNG\r\n\x1a\n")

    def test_missing_media_file_returns_404(self):
        response = self.client.get("/media/does-not-exist.txt")
        self.assertEqual(response.status_code, 404)

    def test_path_traversal_outside_media_root_is_blocked(self):
        response = self.client.get("/media/../../yum_jukebox/settings.py")
        self.assertIn(response.status_code, (400, 404))
        body = (
            b"".join(response.streaming_content)
            if response.streaming
            else response.content
        )
        self.assertNotIn(b"SECRET_KEY", body)

    def test_path_traversal_to_a_real_outside_file_is_blocked(self):
        response = self.client.get("/media/../%s" % CANARY_NAME)
        self.assertIn(response.status_code, (400, 404))
        body = (
            b"".join(response.streaming_content)
            if response.streaming
            else response.content
        )
        self.assertNotIn(CANARY_BYTES, body)

    @skipUnless(os.name == "nt", "os.path.commonpath ValueError cases are Windows-only")
    def test_commonpath_valueerror_paths_do_not_become_500(self):
        # os.path.commonpath raises ValueError for these two shapes, and the
        # except clause in yum_jukebox.urls._media_view is the only thing keeping
        # them from being 500s. Neither target has to exist: the guard rejects
        # before any stat.
        root_drive = os.path.splitdrive(os.path.abspath(self.media_root))[0].upper()
        other_drive = "Z:" if root_drive == "C:" else "C:"
        urls = [
            # A drive-absolute path makes os.path.join discard MEDIA_ROOT, so
            # commonpath is handed two different drives and raises.
            "/media/%s/definitely-missing-payload.bin" % other_drive,
            # A UNC path is absolute as well, which raises the same way.
            "/media/\\\\media_evil\\share.txt",
        ]
        for url in urls:
            with self.subTest(url=url):
                try:
                    response = self.client.get(url)
                except ValueError as exc:
                    # The test client re-raises; in production this is a 500.
                    self.fail("uncaught %s from os.path.commonpath (a 500 in production)" % exc)
                self.assertIn(response.status_code, (400, 404))

    def test_media_route_does_not_shadow_application_urls(self):
        self.assertEqual(self.client.get("/healthz/").status_code, 200)
        self.assertEqual(self.client.get("/accounts/login/").status_code, 200)
