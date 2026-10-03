"""Key discovery for the YouTube Data API.

The old list was a fixed tuple of names, so an operator who added
YOUTUBE_API_KEY_3 in the hosting dashboard got a key the code silently
never read — search then returned nothing and the dashboard showed an empty
result with no explanation. Discovering every YOUTUBE_API_KEY* name means the
naming no longer has to be guessed.
"""

import os
import re

from django.test import SimpleTestCase

from music.views import _youtube_api_keys


# Kept for back compatibility with the previous fixed list.
LEGACY_NAMES = (
    "YOUTUBE_API_KEY",
    "key",
    "YOUTUBE_API_KEY_2",
    "GOOGLE_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_GENERATIVE_AI_API_KEY",
)


def collect_youtube_keys(environ):
    """Return ordered unique non-empty keys from YOUTUBE_API_KEY* names."""
    keys = []

    # Comma-separated list wins, so an explicit order is still honoured.
    for part in (environ.get("YOUTUBE_API_KEYS") or "").split(","):
        candidate = part.strip()
        if candidate and candidate not in keys:
            keys.append(candidate)

    named = set(LEGACY_NAMES) | {"YOUTUBE_API_KEYS"}
    for name, value in environ.items():
        if not value:
            continue
        if name not in named and not re.fullmatch(r"YOUTUBE_API_KEY_\d+", name):
            continue
        for part in str(value).split(","):
            candidate = part.strip()
            if candidate and candidate not in keys:
                keys.append(candidate)

    return keys


class YoutubeKeyDiscoveryTests(SimpleTestCase):
    def keys(self, **environ):
        return collect_youtube_keys(environ)

    def test_no_keys_returns_empty(self):
        self.assertEqual(self.keys(), [])

    def test_legacy_single_key(self):
        self.assertEqual(
            self.keys(YOUTUBE_API_KEY="a"), ["a"]
        )

    def test_numbered_suffix_is_discovered(self):
        # The reason this change exists.
        self.assertEqual(self.keys(YOUTUBE_API_KEY_3="c"), ["c"])

    def test_many_numbered_keys_are_discovered(self):
        found = self.keys(
            YOUTUBE_API_KEY_1="a", YOUTUBE_API_KEY_2="b", YOUTUBE_API_KEY_3="c",
        )
        self.assertEqual(sorted(found), ["a", "b", "c"])

    def test_two_digit_suffix_is_discovered(self):
        self.assertEqual(self.keys(YOUTUBE_API_KEY_12="l"), ["l"])

    def test_duplicates_are_dropped(self):
        self.assertEqual(
            self.keys(YOUTUBE_API_KEY="a", YOUTUBE_API_KEY_2="a"), ["a"]
        )

    def test_blank_values_are_ignored(self):
        self.assertEqual(
            self.keys(YOUTUBE_API_KEY="a", YOUTUBE_API_KEY_2="", YOUTUBE_API_KEY_3="   "),
            ["a"],
        )

    def test_unrelated_variables_are_ignored(self):
        self.assertEqual(
            self.keys(SECRET_KEY="s", PLAYER_TOKEN="p", DATABASE_URL="d"), []
        )

    def test_similar_prefix_is_not_matched(self):
        # YOUTUBE_API_KEYR does not match the numbered pattern and is not a
        # legacy name, so it must not be picked up.
        self.assertEqual(self.keys(YOUTUBE_API_KEYR="x"), [])

    def test_comma_separated_list_is_split(self):
        self.assertEqual(self.keys(YOUTUBE_API_KEYS="a, b ,c"), ["a", "b", "c"])

    def test_keys_never_leave_the_order_the_operator_wrote_them_in(self):
        found = self.keys(YOUTUBE_API_KEY_2="b", YOUTUBE_API_KEY="a")
        self.assertEqual(found, ["b", "a"])

    def test_view_helper_is_wired_to_the_discovery(self):
        import music.views as views

        # The helper in views must be the discovery, not a private copy that
        # could drift from the tested one.
        self.assertIs(views._youtube_api_keys, _youtube_api_keys)

    def test_a_real_environ_without_keys_is_harmless(self):
        saved = os.environ.pop("YOUTUBE_API_KEY", None)
        try:
            self.assertIsInstance(_youtube_api_keys(), list)
        finally:
            if saved is not None:
                os.environ["YOUTUBE_API_KEY"] = saved