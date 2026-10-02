"""Regression tests for every password input that rendered unstyled.

UserCreationForm and PasswordChangeForm build their password fields through
SetPasswordMixin.create_password_fields(), which declares them as fields rather
than reading them off a model. A Meta.widgets entry never reaches them, so each
one rendered with no class at all: no bg-white and no text colour, leaving the
typed value white on white and invisible.

Covers all three forms that show a password box: register, the admin user form,
and change password.
"""

from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.test import TestCase

from music.forms import RegisterForm, UserCreateForm, style_password_fields

# The typed value has to be an explicit dark token in light mode, otherwise it
# inherits the dark-mode colour and disappears against the white background.
DARK_TEXT = "text-slate-900"
LIGHT_BG = "bg-white"


class PasswordInputStyleMixin:
    def assertStyled(self, form, *field_names):
        for name in field_names:
            with self.subTest(field=name):
                classes = form[name].field.widget.attrs.get("class", "")
                self.assertIn(LIGHT_BG, classes, f"{name} has no background")
                self.assertIn(DARK_TEXT, classes, f"{name} text is invisible")
                for token in ("border", "rounded-xl", "px-3", "py-3"):
                    self.assertIn(token, classes, f"{name} lost {token!r}")

    @staticmethod
    def passwordTags(html, names):
        """<input ...> tags for the named password fields.

        Attribute order is not fixed, so match on the whole tag rather than on
        a class-first prefix.
        """
        out = {}
        for chunk in html.split("<input")[1:]:
            tag = chunk.split(">")[0]
            if 'type="password"' not in tag:
                continue
            for name in names:
                if f'name="{name}"' in tag:
                    out[name] = tag
        return out


class RegisterPasswordStyleTests(PasswordInputStyleMixin, TestCase):
    def test_both_password_fields_are_styled(self):
        self.assertStyled(RegisterForm(), "password1", "password2")

    def test_password_classes_match_username(self):
        form = RegisterForm()
        self.assertEqual(
            form["password1"].field.widget.attrs["class"],
            form["username"].field.widget.attrs["class"],
        )

    def test_register_page_serves_styled_inputs(self):
        html = self.client.get("/accounts/register/").content.decode()
        tags = self.passwordTags(html, ("password1", "password2"))
        self.assertEqual(sorted(tags), ["password1", "password2"])
        for name, tag in tags.items():
            with self.subTest(field=name):
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


class AdminUserCreatePasswordStyleTests(PasswordInputStyleMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user("styleadmin", password="pw-12345")
        cls.admin.is_staff = True
        cls.admin.save()
        profile = cls.admin.profile
        profile.role = "admin"
        profile.save()

    def setUp(self):
        self.client.force_login(self.admin)

    def test_both_password_fields_are_styled(self):
        self.assertStyled(UserCreateForm(), "password1", "password2")

    def test_admin_create_page_serves_styled_inputs(self):
        html = self.client.get("/management/users/create/").content.decode()
        tags = self.passwordTags(html, ("password1", "password2"))
        self.assertEqual(sorted(tags), ["password1", "password2"])
        for name, tag in tags.items():
            with self.subTest(field=name):
                self.assertIn(DARK_TEXT, tag, tag)
                self.assertIn(LIGHT_BG, tag, tag)


class ChangePasswordStyleTests(PasswordInputStyleMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("pwchanger", password="pw-12345")

    def setUp(self):
        self.client.force_login(self.user)

    def test_all_three_password_fields_are_styled(self):
        form = style_password_fields(
            PasswordChangeForm(self.user),
            "old_password", "new_password1", "new_password2",
        )
        self.assertStyled(form, "old_password", "new_password1", "new_password2")

    def test_change_password_page_serves_styled_inputs(self):
        html = self.client.get("/accounts/password/").content.decode()
        names = ("old_password", "new_password1", "new_password2")
        tags = self.passwordTags(html, names)
        self.assertEqual(sorted(tags), sorted(names))
        for name, tag in tags.items():
            with self.subTest(field=name):
                self.assertIn(DARK_TEXT, tag, tag)
                self.assertIn(LIGHT_BG, tag, tag)

    def test_posted_form_is_styled_too(self):
        # The view styles the bound form separately, so a failed POST must not
        # bounce back to unstyled boxes.
        response = self.client.post("/accounts/password/", {
            "old_password": "wrong-password",
            "new_password1": "Str0ng-Pass-99",
            "new_password2": "Str0ng-Pass-99",
        })
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        tags = self.passwordTags(html, ("old_password", "new_password1", "new_password2"))
        self.assertEqual(len(tags), 3, tags)
        for name, tag in tags.items():
            with self.subTest(field=name):
                self.assertIn(DARK_TEXT, tag, tag)