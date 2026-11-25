from django.test import TestCase
from django.urls import reverse

from .models import User


def make_user(email="a@example.com", password="pass12345!", **kw):
    return User.objects.create_user(
        email=email, password=password, name="Анна", surname="Иванова", **kw
    )


class AvatarTests(TestCase):
    def test_avatar_generated_on_create(self):
        user = make_user()
        self.assertTrue(user.avatar)
        self.assertTrue(user.avatar.name.startswith("avatars/"))


class AuthTests(TestCase):
    def test_register_logs_in_and_redirects(self):
        resp = self.client.post(
            reverse("users:register"),
            {
                "name": "Боб",
                "surname": "Петров",
                "email": "b@example.com",
                "password": "Str0ng-pass!",
            },
        )
        self.assertRedirects(resp, "/projects/list/", fetch_redirect_response=False)
        self.assertIn("_auth_user_id", self.client.session)

    def test_register_duplicate_email(self):
        make_user("dup@example.com")
        resp = self.client.post(
            reverse("users:register"),
            {
                "name": "Боб",
                "surname": "П",
                "email": "dup@example.com",
                "password": "Str0ng-pass!",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context["form"].errors)

    def test_login_wrong_password(self):
        make_user()
        resp = self.client.post(
            reverse("users:login"), {"email": "a@example.com", "password": "bad"}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(
            "Неверный имейл или пароль", resp.context["form"].non_field_errors()
        )

    def test_login_ok_and_logout(self):
        make_user()
        resp = self.client.post(
            reverse("users:login"), {"email": "a@example.com", "password": "pass12345!"}
        )
        self.assertRedirects(resp, "/projects/list/", fetch_redirect_response=False)
        resp = self.client.get(reverse("users:logout"))
        self.assertRedirects(resp, "/projects/list/", fetch_redirect_response=False)
        self.assertNotIn("_auth_user_id", self.client.session)


class ProfileTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)

    def _post(self, **over):
        data = {
            "name": "Анна",
            "surname": "Иванова",
            "about": "",
            "phone": "",
            "github_url": "",
        }
        data.update(over)
        return self.client.post(reverse("users:edit_profile"), data)

    def test_phone_normalized(self):
        resp = self._post(phone="89991234567")
        self.assertRedirects(
            resp, f"/users/{self.user.pk}/", fetch_redirect_response=False
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone, "+79991234567")

    def test_phone_bad_format(self):
        self.assertTrue(self._post(phone="12345").context["form"].errors.get("phone"))

    def test_phone_unique_across_formats(self):
        make_user("o@example.com", phone="+79991234567")
        self.assertTrue(
            self._post(phone="89991234567").context["form"].errors.get("phone")
        )

    def test_github_must_be_github(self):
        self.assertTrue(
            self._post(github_url="https://example.com/x")
            .context["form"]
            .errors.get("github_url")
        )
        self.assertEqual(self._post(github_url="https://github.com/x").status_code, 302)

    def test_edit_requires_login(self):
        self.client.logout()
        self.assertEqual(
            self.client.get(reverse("users:edit_profile")).status_code, 302
        )


class UserListTests(TestCase):
    def test_pagination_12(self):
        for i in range(15):
            make_user(f"u{i}@example.com")
        resp = self.client.get(reverse("users:list"))
        self.assertEqual(len(resp.context["page_obj"]), 12)

    def test_detail_404(self):
        self.assertEqual(self.client.get("/users/999/").status_code, 404)

    def test_change_password(self):
        user = make_user()
        self.client.force_login(user)
        resp = self.client.post(
            reverse("users:change_password"),
            {
                "old_password": "pass12345!",
                "new_password1": "N3w-strong-pass",
                "new_password2": "N3w-strong-pass",
            },
        )
        self.assertRedirects(resp, f"/users/{user.pk}/", fetch_redirect_response=False)
        user.refresh_from_db()
        self.assertTrue(user.check_password("N3w-strong-pass"))
