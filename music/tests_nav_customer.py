from django.contrib.auth.models import AnonymousUser, User
from django.test import RequestFactory, TestCase
from django.template.loader import render_to_string
from django.urls import reverse

from music.models import Profile


class LoginPageRegistrationEntryTests(TestCase):
    def test_login_page_links_to_register(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("register"))

    def test_login_page_has_no_dead_end_link_to_login_gated_root(self):
        response = self.client.get(reverse("login"))
        self.assertNotContains(response, 'href="/"')

    def test_login_page_hides_register_cta_from_authenticated_user(self):
        # LoginView has no redirect_authenticated_user, so it returns 200 for a
        # logged-in user; a signed-in user must not be invited to register again
        User.objects.create_user(username="auth_l", password="testpass123")
        self.client.login(username="auth_l", password="testpass123")
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, reverse("register"))


class PlayerPageAuthEntryTests(TestCase):
    def test_player_anonymous_has_register_link(self):
        response = self.client.get(reverse("player"))
        self.assertEqual(response.status_code, 302)

    def test_player_authenticated_has_dashboard_and_genre_links(self):
        user = User.objects.create_user(username="staff_p", password="testpass123")
        Profile.objects.update_or_create(user=user, defaults={"role": "staff"})
        self.client.login(username="staff_p", password="testpass123")
        response = self.client.get(reverse("player"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("dashboard"))
        self.assertContains(response, reverse("genre_list"))
        # a logged-in user already has an account: the register link is
        # anonymous-only and must not appear in the authenticated header
        self.assertNotContains(response, reverse("register"))

    def test_player_anonymous_branch_offers_login_and_register(self):
        # GET / is login-gated (302), so render the anonymous branch directly to
        # pin that an unauthenticated visitor is offered both account entries.
        request = RequestFactory().get(reverse("player"))
        request.user = AnonymousUser()
        html = render_to_string("music/player.html", request=request)
        self.assertIn(reverse("login"), html)
        self.assertIn(reverse("register"), html)
        self.assertNotIn(reverse("logout"), html)

    def test_player_role_guard_survives_user_without_profile(self):
        user = User.objects.create_user(username="orphan_p", password="testpass123")
        # a post_save signal creates the Profile row; delete it so the template's
        # {% with role=user.profile.role %} guard is actually exercised
        Profile.objects.filter(user=user).delete()
        self.client.login(username="orphan_p", password="testpass123")
        response = self.client.get(reverse("player"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "แนวเพลง")


class RequestPageAuthEntryTests(TestCase):
    def test_request_page_anonymous_has_login_and_register(self):
        response = self.client.get(reverse("request_view"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("login"))
        self.assertContains(response, reverse("register"))

    def test_request_page_authenticated_has_logout_form(self):
        user = User.objects.create_user(username="cust_r", password="testpass123")
        Profile.objects.update_or_create(user=user, defaults={"role": "customer"})
        self.client.login(username="cust_r", password="testpass123")
        response = self.client.get(reverse("request_view"))
        self.assertContains(response, reverse("logout"))
        self.assertContains(response, "cust_r")
        # a signed-in user already has an account: no register link here either
        self.assertNotContains(response, reverse("register"))

    def test_request_page_header_wraps_on_narrow_screens(self):
        # the header row holds logo + title + toggle + auth controls inside a
        # max-w-sm column on a body with overflow-x-hidden, so without
        # flex-wrap the extras are clipped rather than reflowed
        response = self.client.get(reverse("request_view"))
        self.assertContains(response, "flex flex-wrap items-center gap-3 mb-6")


class RegisterPageLoginLinkTests(TestCase):
    def test_register_page_body_links_back_to_login(self):
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)
        # register.html extends base.html, whose navbar also links to login, so
        # anchor on the register template's OWN body link (its own wording and
        # its own amber classes) to avoid asserting on the navbar instead.
        self.assertContains(response, "มีบัญชีแล้ว?")
        self.assertContains(
            response, f'มีบัญชีแล้ว? <a href="{reverse("login")}"'
        )
