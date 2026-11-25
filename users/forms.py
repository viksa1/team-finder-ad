from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.password_validation import validate_password

from .models import User
from .validators import normalize_phone, validate_github_url


# форма регистрации
class RegisterForm(forms.ModelForm):
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["name", "surname", "email", "password"]

    # проверка, есть ли пользователь с такой же почтой
    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже существует.")
        return email

    # проверка сложности пароля
    def clean_password(self):
        password = self.cleaned_data["password"]
        validate_password(password)
        return password

    # если проверки пройдены - сохраняем пользователя
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


# Форма входа
class LoginForm(forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.user = None

    # ищет пользователя и проверяет введённый пароль
    def clean(self):
        cleaned = super().clean()
        email = cleaned.get("email")
        password = cleaned.get("password")
        if email and password:
            self.user = authenticate(self.request, username=email, password=password)
            if self.user is None:
                raise forms.ValidationError("Неверный имейл или пароль")
        return cleaned


# форма редактирования профиля
class ProfileEditForm(forms.ModelForm):
    avatar = forms.ImageField(label="Аватар", required=False)

    class Meta:
        model = User
        fields = ["name", "surname", "avatar", "about", "phone", "github_url"]
        widgets = {"about": forms.Textarea(attrs={"rows": 4, "maxlength": 256})}

    def clean_phone(self):
        phone = (self.cleaned_data.get("phone") or "").strip()
        if not phone:
            return None
        phone = normalize_phone(phone)
        # после нормализации 8... и +7... - один номер, дальше проврека на уникальность
        if User.objects.filter(phone=phone).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(
                "Пользователь с таким номером телефона уже существует."
            )
        return phone

    # проверка ссылки на github
    def clean_github_url(self):
        url = (self.cleaned_data.get("github_url") or "").strip()
        validate_github_url(url)
        return url

    # страница о себе не превышает 256 символов
    def clean_about(self):
        about = self.cleaned_data.get("about", "")
        if len(about) > 256:
            raise forms.ValidationError("Не более 256 символов.")
        return about


# страница смены пароля
# наследуется от встроенной формы Django PasswordChangeForm
class ChangePasswordForm(PasswordChangeForm):
    """Поля: old_password, new_password1, new_password2."""
