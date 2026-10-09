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
