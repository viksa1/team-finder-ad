import json
from urllib.parse import quote

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from .forms import ProjectForm
from .models import Project, Skill


def project_list(request):
    projects = (
        Project.objects.select_related("owner")
        .prefetch_related("participants", "skills")
        .order_by("-created_at", "-id")
    )
    active_skill = request.GET.get("skill") or None
    if active_skill:
        projects = projects.filter(skills__name=active_skill).distinct()

    page_obj = Paginator(projects, settings.PROJECTS_PER_PAGE).get_page(
        request.GET.get("page")
    )
    query_prefix = f"skill={quote(active_skill)}&" if active_skill else ""

    return render(
        request,
        "projects/project_list.html",
        {
            "projects": projects,
            "page_obj": page_obj,
            "all_skills": Skill.objects.order_by("name")
            .values_list("name", flat=True)
            .distinct(),
            "active_skill": active_skill,
            "query_prefix": query_prefix,
        },
    )


def project_detail(request, project_id):
    project = get_object_or_404(
        Project.objects.select_related("owner").prefetch_related(
            "participants", "skills"
        ),
        pk=project_id,
    )
    return render(request, "projects/project-details.html", {"project": project})


def _can_edit(user, project):
    return user.is_authenticated and (user.is_staff or project.owner_id == user.pk)


@login_required
def create_project(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            project.participants.add(request.user)
            return redirect("projects:detail", project_id=project.pk)
    else:
        form = ProjectForm()
    return render(
        request, "projects/create-project.html", {"form": form, "is_edit": False}
    )


@login_required
def edit_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if not _can_edit(request.user, project):
        return HttpResponseForbidden("Редактировать проект может только его автор.")
    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return redirect("projects:detail", project_id=project.pk)
    else:
        form = ProjectForm(instance=project)
    return render(
        request, "projects/create-project.html", {"form": form, "is_edit": True}
    )


def _json_error(message, status):
    return JsonResponse({"status": "error", "error": message}, status=status)


def _auth_required(request):
    if not request.user.is_authenticated:
        return _json_error("Требуется авторизация", 401)
    return None


def _body_params(request):
    if request.content_type == "application/json":
        try:
            data = json.loads(request.body or b"{}")
        except ValueError:
            return {}
        return data if isinstance(data, dict) else {}
    return request.POST


@require_POST
def complete_project(request, project_id):
    if resp := _auth_required(request):
        return resp
    project = get_object_or_404(Project, pk=project_id)
    if project.owner_id != request.user.pk:
        return _json_error("Недостаточно прав", 403)
    if project.status != Project.Status.OPEN:
        return _json_error("Проект уже закрыт", 400)
    project.status = Project.Status.CLOSED
    project.save(update_fields=["status"])
    return JsonResponse({"status": "ok", "project_status": "closed"})


@require_POST
def toggle_participate(request, project_id):
    if resp := _auth_required(request):
        return resp
    project = get_object_or_404(Project, pk=project_id)
    if project.participants.filter(pk=request.user.pk).exists():
        project.participants.remove(request.user)
        participant = False
    else:
        project.participants.add(request.user)
        participant = True
    return JsonResponse({"status": "ok", "participant": participant})


@require_GET
def skill_autocomplete(request):
    q = request.GET.get("q", "").strip()
    skills = (
        Skill.objects.filter(name__istartswith=q)
        .order_by("name")
        .values("id", "name")[:10]
    )
    return JsonResponse(list(skills), safe=False)


@require_POST
def add_skill(request, project_id):
    if resp := _auth_required(request):
        return resp
    project = get_object_or_404(Project, pk=project_id)
    if project.owner_id != request.user.pk:
        return _json_error("Недостаточно прав", 403)

    params = _body_params(request)
    skill_id = params.get("skill_id")
    name = (
        (params.get("name") or "").strip()
        if isinstance(params.get("name"), str)
        else ""
    )

    created = False
    if skill_id not in (None, ""):
        try:
            skill = Skill.objects.get(pk=int(skill_id))
        except (Skill.DoesNotExist, ValueError, TypeError):
            return _json_error("Навык не найден", 404)
    elif name:
        if len(name) > 124:
            return _json_error("Название навыка слишком длинное", 400)
        skill = Skill.objects.filter(name__iexact=name).first()
        if skill is None:
            skill = Skill.objects.create(name=name)
            created = True
    else:
        return _json_error("Нужен skill_id или name", 400)

    added = not project.skills.filter(pk=skill.pk).exists()
    if added:
        project.skills.add(skill)
    return JsonResponse({"skill_id": skill.pk, "created": created, "added": added})


@require_POST
def remove_skill(request, project_id, skill_id):
    if resp := _auth_required(request):
        return resp
    project = get_object_or_404(Project, pk=project_id)
    if project.owner_id != request.user.pk:
        return _json_error("Недостаточно прав", 403)
    skill = get_object_or_404(Skill, pk=skill_id)
    if not project.skills.filter(pk=skill.pk).exists():
        return _json_error("Навык не добавлен в проект", 400)
    project.skills.remove(skill)
    return JsonResponse({"status": "ok"})
