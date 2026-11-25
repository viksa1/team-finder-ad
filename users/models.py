import uuid

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models

from .avatars import generate_avatar


# Класс для создания пользователей в базе данных
class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Email обязателен")
        # нормализация почты
        user = self.model(email=self.normalize_email(email), **extra_fields)
        # хеширование пароля
        user.set_password(password)
        user.save(using=self._db)
        return user

    # создание обычного пользователя
    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    # создание суперпользователя
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("name", "Admin")
        extra_fields.setdefault("surname", "Admin")
        return self._create_user(email, password, **extra_fields)


# Модель пользователя
# Из AbstractBaseUser наследуются поля password и last_login
# Из PermissionsMixin наследуются права доступа
class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField("Email", unique=True)
    name = models.CharField("Имя", max_length=124)
    surname = models.CharField("Фамилия", max_length=124)
    avatar = models.ImageField("Аватар", upload_to="avatars/")
    phone = models.CharField(
        "Телефон", max_length=12, unique=True, null=True, blank=True
    )
    github_url = models.URLField("Ссылка на GitHub", blank=True)
    about = models.TextField("О себе", max_length=256, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return f"{self.name} {self.surname} <{self.email}>"

    # функция генерации аватарки, если пользователь не загрузил её при регистрации
    def save(self, *args, **kwargs):
        if not self.avatar:
            self.avatar.save(
                f"avatar_{uuid.uuid4()}.png", generate_avatar(self.name), save=False
            )
        super().save(*args, **kwargs)
