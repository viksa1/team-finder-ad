from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import AdminPasswordChangeForm

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    change_password_form = AdminPasswordChangeForm
    ordering = ("id",)
    list_display = ("id", "email", "name", "surname", "is_active", "is_staff")
    search_fields = ("email", "name", "surname")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Профиль",
            {"fields": ("name", "surname", "avatar", "phone", "github_url", "about")},
        ),
        (
            "Права",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "name",
                    "surname",
                    "password1",
                    "password2",
                    "is_staff",
                ),
            },
        ),
    )
