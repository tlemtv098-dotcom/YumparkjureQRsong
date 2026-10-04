"""Regression test for the search results being wiped by a superseded request.

Typing schedules a search 500 ms later, and pressing the button or Enter fires
another one immediately. The first request is aborted, but its rejection still
ran afterwards and cleared #manual-results — which the newer request had already
filled. The panel therefore looked empty even though the search worked.

The guard is a monotonically increasing sequence number: a response whose
number is not the current one returns before touching the DOM.
"""

import re

from django.contrib.auth.models import User
from django.test import TestCase


class PlayerSearchRaceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user("raceadmin", password="pw-12345")
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

    def test_sequence_counter_exists(self):
        self.assertIn("let manualSearchSeq = 0;", self.playerHtml())

    def test_each_search_takes_a_new_sequence_number(self):
        html = self.playerHtml()
        self.assertIn("const seq = ++manualSearchSeq;", html)

    def test_success_handler_ignores_a_superseded_response(self):
        block = self.manualSearchBlock()
        handler = block[block.index(".then(data => {"):]
        self.assertIn(
            "if (seq !== manualSearchSeq)", handler,
            "a stale response would clear the newer results",
        )
        # The guard has to come before the container is written.
        self.assertLess(
            handler.index("if (seq !== manualSearchSeq)"),
            handler.index("manualSearchResults = data.results"),
        )
        # ...and the guard must actually return, not just be mentioned.
        guard = handler[handler.index("if (seq !== manualSearchSeq)"):]
        self.assertLess(
            guard.index("return;"), guard.index("manualSearchResults"),
            "the guard does not stop the stale response",
        )

    def manualSearchBlock(self):
        """The manualSearch function body only.

        Other handlers in the page also have .catch blocks, so slice from the
        function declaration rather than matching .catch on its own.
        """
        html = self.playerHtml()
        start = html.index("function manualSearch() {")
        end = html.index("function manualPlay(idx)", start)
        return html[start:end]

    def test_error_handler_ignores_a_superseded_response(self):
        block = self.manualSearchBlock()
        handler = block[block.index(".catch(err => {"):]
        self.assertIn(
            "if (seq !== manualSearchSeq) return;",
            handler,
            "the aborted predecessor's catch still cleared the container",
        )
        self.assertLess(
            handler.index("if (seq !== manualSearchSeq) return;"),
            handler.index('classList.add("hidden")'),
        )

    def test_abort_still_short_circuits_for_the_current_request(self):
        # The seq guard must not swallow the legitimate AbortError branch.
        block = self.manualSearchBlock()
        self.assertIn('if (err && err.name === "AbortError") return;', block)
        # It has to come before the retry is scheduled, otherwise a cancelled
        # request would fire a second one.
        abort = block.index('if (err && err.name === "AbortError") return;')
        retry = block.index("setTimeout(() => manualSearchRetry(true), 800)")
        self.assertLess(abort, retry)

    def test_button_and_typing_can_both_fire_without_emptying_results(self):
        html = self.playerHtml()
        # Both the debounced input handler and the button call manualSearch;
        # the sequence guard is what makes the overlap safe.
        self.assertIn("manualSearchTimer = setTimeout(manualSearch, 500)", html)
        self.assertIn("manualSearch();", html)
        self.assertIn("const seq = ++manualSearchSeq;", html)

    def test_results_container_still_exists_and_is_written(self):
        html = self.playerHtml()
        self.assertIn('id="manual-results"', html)
        self.assertIn('document.getElementById("manual-results")', html)