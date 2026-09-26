from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from music.models import Profile


class BaseNavTests(TestCase):
    def _make_user(self, username, role):
        user = User.objects.create_user(username=username, password="testpass123")
        Profile.objects.update_or_create(user=user, defaults={"role": role})
        return user

    def test_anonymous_register_page_has_link_to_login(self):
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)
        # The navbar itself, not just the pre-existing "already have an account?" link
        # in register.html: pin the nav element, the brand link and the register link.
        self.assertContains(response, "<nav")
        self.assertContains(response, reverse("player"))
        self.assertContains(response, 'href="/"')
        self.assertContains(response, reverse("register"))
        self.assertContains(response, reverse("login"))

    def test_anonymous_register_page_has_no_management_links(self):
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, reverse("genre_list"))
        self.assertNotContains(response, reverse("user_list"))

    def test_customer_nav_shows_no_management_links(self):
        self._make_user("cust_nav", "customer")
        self.client.login(username="cust_nav", password="testpass123")
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, reverse("genre_list"))
        self.assertNotContains(response, reverse("user_list"))

    def test_staff_nav_shows_genre_and_tag_links(self):
        self._make_user("staff_nav", "staff")
        self.client.login(username="staff_nav", password="testpass123")
        response = self.client.get(reverse("profile"))
        self.assertContains(response, reverse("genre_list"))
        self.assertContains(response, reverse("tag_list"))
        self.assertNotContains(response, reverse("user_list"))

    def test_admin_nav_shows_user_management(self):
        self._make_user("admin_nav", "admin")
        self.client.login(username="admin_nav", password="testpass123")
        response = self.client.get(reverse("profile"))
        self.assertContains(response, reverse("user_list"))

    def test_messages_container_is_rendered(self):
        response = self.client.get(reverse("register"))
        self.assertContains(response, "messages")
