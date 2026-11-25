from django.conf import settings
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ChangePasswordForm, LoginForm, ProfileEditForm, RegisterForm
from .models import User

# регистрация
def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            return redirect("/users/login/")
    else:
        form = RegisterForm()
    return render(request, "users/register.html", {"form": form})

# проверка логина и пароля
def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST, request=request)
        if form.is_valid():
            login(request, form.user)
            return redirect("/projects/list/")
    else:
        form = LoginForm(request=request)
    return render(request, "users/login.html", {"form": form})


# выход из аккаунта
def logout_view(request):
    logout(request)
    return redirect("/projects/list/")

# профиль
def user_detail(request, user_id):
    profile_user = get_object_or_404(User, pk=user_id)
    return render(request, "users/user-details.html", {"user": profile_user})


# редактирование профиля
@login_required
def edit_profile(request):
    if request.method == "POST":
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("users:detail", user_id=request.user.pk)
    else:
        form = ProfileEditForm(instance=request.user)
    return render(request, "users/edit_profile.html", {"form": form, "from": form})

# смена пароля
@login_required
def change_password(request):
    if request.method == "POST":
        form = ChangePasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return redirect("users:detail", user_id=user.pk)
    else:
        form = ChangePasswordForm(request.user)
    return render(request, "users/change_password.html", {"form": form, "from": form})

# список участников
def user_list(request):
    users = User.objects.order_by("id")
    page_obj = Paginator(users, settings.USERS_PER_PAGE).get_page(
        request.GET.get("page")
    )
    return render(
        request,
        "users/participants.html",
        {"participants": users, "page_obj": page_obj, "query_prefix": ""},
    )
