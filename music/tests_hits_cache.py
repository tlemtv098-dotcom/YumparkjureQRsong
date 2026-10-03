"""Regression tests for the recommendations cache.

The player asked for recommendations on DOMContentLoaded, then every 60
seconds, on every tab switch, and after a few queue mutations. Each call
fans out to several YouTube searches, and a search costs 100 units of a
10,000 unit daily quota, so the whole day was gone within minutes and manual
search then returned nothing.

The payload is now cached in localStorage for 15 minutes and every automatic
path goes through loadHits(), which reads the cache first.
"""

import re

from django.contrib.auth.models import User
from django.test import TestCase


class HitsCacheTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user("cacheadmin", password="pw-12345")
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

    def test_cache_helpers_exist(self):
        html = self.playerHtml()
        for symbol in (
            "const HITS_CACHE_KEY = 'hitsCache'",
            "const HITS_CACHE_TTL_MS = 15 * 60 * 1000",
            "function readHitsCache()",
            "function writeHitsCache(",
            "function loadHits(",
        ):
            with self.subTest(symbol=symbol):
                self.assertIn(symbol, html)

    def test_successful_response_is_cached(self):
        html = self.playerHtml()
        handler = re.search(
            r"if \(data\.results && data\.results\.length > 0\) \{.*?\}", html, re.S
        ).group(0)
        self.assertIn("writeHitsCache(filtered);", handler)

    def test_page_load_uses_the_cache(self):
        html = self.playerHtml()
        block = re.search(
            r'document\.addEventListener\("DOMContentLoaded".*?\}\);', html, re.S
        ).group(0)
        self.assertIn("loadHits(false);", block)
        self.assertNotIn("fetchHits(true);", block)

    def test_no_sixty_second_polling_loop(self):
        # The old setInterval(fetchHits, 60000) was the largest single drain.
        html = self.playerHtml()
        self.assertNotIn("setInterval(fetchHits, 60000)", html)
        self.assertIn("setInterval(() => loadHits(false), HITS_CACHE_TTL_MS)", html)

    def test_tab_switch_uses_the_cache(self):
        html = self.playerHtml()
        # Several visibilitychange handlers exist; pick the one that refetches.
        handlers = re.findall(
            r"document\.addEventListener\('visibilitychange'.*?\n        \}\);", html, re.S
        )
        refetching = [h for h in handlers if "loadHits" in h]
        self.assertEqual(len(refetching), 1, f"no cache-aware refetch: {handlers}")
        self.assertNotIn("fetchHits()", refetching[0])

    def test_opening_the_search_panel_uses_the_cache(self):
        html = self.playerHtml()
        handler = re.search(r"function toggleSearchPanel\(\).*?\n        \}", html, re.S).group(0)
        self.assertIn("loadHits(false);", handler)
        self.assertNotIn("fetchHits();", handler)

    def test_loadHits_falls_back_to_the_network_when_stale(self):
        html = self.playerHtml()
        handler = re.search(r"function loadHits\(fresh\) \{.*?\n        \}", html, re.S).group(0)
        self.assertIn("const cached = (!fresh) ? readHitsCache() : null;", handler)
        self.assertIn("fetchHits(fresh);", handler)

    def test_fresh_requests_bypass_the_cache(self):
        # A cached list has already been shown, so "give me new ones" has to hit
        # the network even when a cache entry exists.
        html = self.playerHtml()
        handler = re.search(r"function loadHits\(fresh\) \{.*?\n        \}", html, re.S).group(0)
        self.assertIn("(!fresh)", handler)
        # The manual refresh button still forces a network call.
        self.assertIn('onclick="fetchHits(true)"', html)

    def test_expired_cache_is_ignored(self):
        html = self.playerHtml()
        handler = re.search(r"function readHitsCache\(\) \{.*?\n        \}", html, re.S).group(0)
        self.assertIn("HITS_CACHE_TTL_MS", handler)
        self.assertIn("return null;", handler)

    def test_corrupt_cache_does_not_throw(self):
        html = self.playerHtml()
        handler = re.search(r"function readHitsCache\(\) \{.*?\n        \}", html, re.S).group(0)
        self.assertIn("catch (e)", handler)

    def test_cache_write_failure_does_not_throw(self):
        html = self.playerHtml()
        handler = re.search(r"function writeHitsCache\(.*?\n        \}", html, re.S).group(0)
        self.assertIn("catch (e)", handler)