"""Regression tests for the unstyled password inputs on the register page.

UserCreationForm builds password1/password2 through
SetPasswordMixin.create_password_fields(), which declares them as fields
rather than pulling them off the model. Meta.widgets therefore never reaches
them, so they rendered with no class at all: no bg-white and no text colour,
leaving white text on a white background.
"""

from django.contrib.auth.models import User
from django.test import TestCase

from music.forms import RegisterForm

# The text colour has to be an explicit dark token in light mode, otherwise
# the browser inherits the dark-mode text colour and the typed value vanishes.
DARK_TEXT = "text-slate-900"
LIGHT_BG = "bg-white"


class RegisterPasswordFieldStyleTests(TestCase):
    def widgetClasses(self, field_name):
        return self.__class__.form()[field_name].field.widget.attrs.get("class", "")

    @classmethod
    def form(cls):
        return RegisterForm()

    def assertStyled(self, field_name):
        classes = self.widgetClasses(field_name)
        for token in (LIGHT_BG, DARK_TEXT, "border", "rounded-xl", "px-3", "py-3"):
            self.assertIn(token, classes, f"{field_name} lost {token!r}: {classes!r}")

    def test_password1_has_a_white_background(self):
        self.assertIn(LIGHT_BG, self.widgetClasses("password1"))

    def test_password1_text_is_dark(self):
        self.assertIn(DARK_TEXT, self.widgetClasses("password1"))

    def test_password2_has_a_white_background(self):
        self.assertIn(LIGHT_BG, self.widgetClasses("password2"))

    def test_password2_text_is_dark(self):
        self.assertIn(DARK_TEXT, self.widgetClasses("password2"))

    def test_password_fields_match_the_other_fields(self):
        # If the styling ever drifts from the rest of the form again, the two
        # password boxes are the ones that turn invisible.
        reference = self.widgetClasses("username")
        for field in ("password1", "password2"):
            self.assertEqual(
                self.widgetClasses(field), reference,
                f"{field} no longer matches the other inputs",
            )

    def test_rendered_html_keeps_text_colour_on_password_inputs(self):
        html = RegisterForm().as_p()
        for tag in self.passwordTags(html):
            self.assertIn(DARK_TEXT, tag, tag)
            self.assertIn(LIGHT_BG, tag, tag)

    @staticmethod
    def passwordTags(html):
        """Every <input ...> tag carrying type="password".

        Attribute order is not fixed, so match on the tag rather than on a
        class-first prefix.
        """
        return [
            chunk.split(">")[0]
            for chunk in html.split("<input")[1:]
            if 'type="password"' in chunk.split(">")[0]
        ]

    def test_register_page_serves_styled_password_inputs(self):
        response = self.client.get("/accounts/register/")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        password_tags = self.passwordTags(html)
        # The page also renders the admin's own password-reset form in some
        # layouts, so assert on the register fields by name rather than count.
        by_name = [t for t in password_tags if 'name="password1"' in t or 'name="password2"' in t]
        self.assertEqual(len(by_name), 2, password_tags)
        for tag in by_name:
            self.assertIn(DARK_TEXT, tag, tag)
            self.assertIn(LIGHT_BG, tag, tag)

    def test_registration_still_succeeds(self):
        response = self.client.post("/accounts/register/", {
            "first_name": "ทดสอบ",
            "last_name": "ระบบ",
            "username": "styletest",
            "email": "styletest@example.com",
            "phone": "0812345678",
            "password1": "Str0ng-Pass-99",
            "password2": "Str0ng-Pass-99",
        })
        self.assertIn(response.status_code, (200, 302))
        self.assertTrue(User.objects.filter(username="styletest").exists())