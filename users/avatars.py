import random
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont

BACKGROUNDS = [
    "#7C9885",
    "#8E9AAF",
    "#B08EA2",
    "#9C8FB5",
    "#C49A7E",
    "#6F9BA8",
    "#A6906F",
    "#7D8CC4",
    "#B5838D",
    "#6B9080",
]
SIZE = 400
FONT_PATH = (
    Path(settings.BASE_DIR)
    / "static"
    / "fonts"
    / "Neue_Haas_Grotesk_Display_Pro_75_Bold.otf"
)


def _load_font(size):
    for candidate in (str(FONT_PATH), "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def generate_avatar(name):
    letter = (name or "?").strip()[:1].upper() or "?"
    image = Image.new("RGB", (SIZE, SIZE), random.choice(BACKGROUNDS))
    draw = ImageDraw.Draw(image)
    font = _load_font(int(SIZE * 0.5))
    draw.text((SIZE / 2, SIZE / 2), letter, font=font, fill="white", anchor="mm")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return ContentFile(buffer.getvalue())
