import re
from urllib.parse import urlparse

from django.core.exceptions import ValidationError

PHONE_RE = re.compile(r"^(?:8|\+7)\d{10}$")


# проверка ссылки на github
def validate_github_url(value):
    if not value:
        return
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in ("http", "https") or not host:
        raise ValidationError("Введите корректную ссылку.")
    if host not in ("github.com", "www.github.com"):
        raise ValidationError("Ссылка должна вести на GitHub (github.com).")


# проверка формата телефона
def normalize_phone(value):
    value = (value or "").strip()
    if not PHONE_RE.match(value):
        raise ValidationError(
            "Номер телефона должен быть в формате 8XXXXXXXXXX или +7XXXXXXXXXX."
        )
    if value.startswith("8"):
        value = "+7" + value[1:]
    return value
