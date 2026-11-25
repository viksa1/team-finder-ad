import json

from django.test import TestCase
from django.urls import reverse

from users.models import User

from .models import Project, Skill


def make_user(email):
    return User.objects.create_user(
        email=email, password="pass12345!", name="Имя", surname="Фам"
    )


class ProjectViewsTests(TestCase):
    def setUp(self):
        self.owner = make_user("owner@example.com")
        self.other = make_user("other@example.com")

    def test_root_redirects(self):
        self.assertRedirects(
            self.client.get("/"), "/projects/list/", fetch_redirect_response=False
        )

    def test_list_order_pagination_and_filter(self):
        py = Skill.objects.create(name="Python")
        for i in range(13):
            p = Project.objects.create(name=f"P{i}", owner=self.owner)
            if i == 0:
                p.skills.add(py)
        resp = self.client.get(reverse("projects:list"))
        self.assertEqual(len(resp.context["page_obj"]), 12)
        self.assertEqual(resp.context["page_obj"][0].name, "P12")
        resp = self.client.get(reverse("projects:list"), {"skill": "Python"})
        self.assertEqual([p.name for p in resp.context["projects"]], ["P0"])
        self.assertEqual(resp.context["active_skill"], "Python")
        self.assertEqual(list(resp.context["all_skills"]), ["Python"])

    def test_create_sets_owner_and_participant(self):
        self.client.force_login(self.owner)
        resp = self.client.post(
            reverse("projects:create"),
            {"name": "X", "description": "d", "github_url": "", "status": "open"},
        )
        project = Project.objects.get(name="X")
        self.assertRedirects(
            resp, f"/projects/{project.pk}/", fetch_redirect_response=False
        )
        self.assertEqual(project.owner, self.owner)
        self.assertIn(self.owner, project.participants.all())

    def test_create_requires_login(self):
        self.assertEqual(self.client.get(reverse("projects:create")).status_code, 302)

    def test_create_github_validation(self):
        self.client.force_login(self.owner)
        resp = self.client.post(
            reverse("projects:create"),
            {"name": "X", "github_url": "https://gitlab.com/x", "status": "open"},
        )
        self.assertTrue(resp.context["form"].errors.get("github_url"))

    def test_edit_only_owner(self):
        project = Project.objects.create(name="X", owner=self.owner)
        self.client.force_login(self.other)
        self.assertEqual(
            self.client.get(f"/projects/{project.pk}/edit/").status_code, 403
        )
        self.client.force_login(self.owner)
        resp = self.client.get(f"/projects/{project.pk}/edit/")
        self.assertTrue(resp.context["is_edit"])

    def test_toggle_participate(self):
        project = Project.objects.create(name="X", owner=self.owner)
        url = f"/projects/{project.pk}/toggle-participate/"
        self.assertEqual(self.client.post(url).status_code, 401)
        self.client.force_login(self.other)
        self.assertTrue(self.client.post(url).json()["participant"])
        self.assertFalse(self.client.post(url).json()["participant"])

    def test_complete_project(self):
        project = Project.objects.create(name="X", owner=self.owner)
        url = f"/projects/{project.pk}/complete/"
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(url).status_code, 403)
        self.client.force_login(self.owner)
        self.assertEqual(
            self.client.post(url).json(), {"status": "ok", "project_status": "closed"}
        )
        self.assertEqual(self.client.post(url).status_code, 400)


class SkillsApiTests(TestCase):
    def setUp(self):
        self.owner = make_user("owner@example.com")
        self.project = Project.objects.create(name="X", owner=self.owner)

    def test_autocomplete_limit_order_prefix(self):
        for n in ["Zeta"] + [f"Py{i:02d}" for i in range(12)]:
            Skill.objects.create(name=n)
        data = self.client.get("/projects/skills/", {"q": "py"}).json()
        self.assertEqual(len(data), 10)
        self.assertEqual(data[0]["name"], "Py00")
        self.assertEqual(set(data[0]), {"id", "name"})

    def test_add_new_then_existing(self):
        self.client.force_login(self.owner)
        url = f"/projects/{self.project.pk}/skills/add/"
        r = self.client.post(url, {"name": "Django"}).json()
        self.assertEqual((r["created"], r["added"]), (True, True))
        r2 = self.client.post(
            url,
            json.dumps({"skill_id": r["skill_id"]}),
            content_type="application/json",
        ).json()
        self.assertEqual((r2["created"], r2["added"]), (False, False))

    def test_add_permissions(self):
        url = f"/projects/{self.project.pk}/skills/add/"
        self.assertEqual(self.client.post(url, {"name": "A"}).status_code, 401)
        self.client.force_login(make_user("x@example.com"))
        self.assertEqual(self.client.post(url, {"name": "A"}).status_code, 403)

    def test_remove(self):
        skill = Skill.objects.create(name="Go")
        self.project.skills.add(skill)
        url = f"/projects/{self.project.pk}/skills/{skill.pk}/remove/"
        self.client.force_login(self.owner)
        self.assertEqual(self.client.post(url).status_code, 200)
        self.assertTrue(Skill.objects.filter(pk=skill.pk).exists())
        self.assertEqual(self.client.post(url).status_code, 400)
        self.assertEqual(
            self.client.post(
                f"/projects/{self.project.pk}/skills/999/remove/"
            ).status_code,
            404,
        )
