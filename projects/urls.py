from django.shortcuts import redirect
from django.urls import path, re_path

from . import views

app_name = "projects"

urlpatterns = [
    path("", lambda request: redirect("projects:list")),
    path("list/", views.project_list, name="list"),
    path("create-project/", views.create_project, name="create"),
    path("skills/", views.skill_autocomplete, name="skills"),
    path("<int:project_id>/", views.project_detail, name="detail"),
    path("<int:project_id>/edit/", views.edit_project, name="edit"),
    re_path(
        r"^(?P<project_id>\d+)/complete/?$", views.complete_project, name="complete"
    ),
    re_path(
        r"^(?P<project_id>\d+)/toggle-participate/?$",
        views.toggle_participate,
        name="toggle_participate",
    ),
    re_path(r"^(?P<project_id>\d+)/skills/add/?$", views.add_skill, name="skill_add"),
    re_path(
        r"^(?P<project_id>\d+)/skills/(?P<skill_id>\d+)/remove/?$",
        views.remove_skill,
        name="skill_remove",
    ),
]
