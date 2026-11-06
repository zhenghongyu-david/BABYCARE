"""Generate the launcher icon and Android presplash image."""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
FONT = ASSETS / "fonts" / "NotoSansSC-Bold.ttf"
CORAL = (255, 122, 102)
CORAL_DARK = (242, 99, 80)
CREAM = (255, 249, 243)
HONEY = (255, 196, 77)
INK = (48, 43, 56)


def star_points(cx, cy, outer, inner, rotation=-math.pi / 2):
    points = []
    for i in range(10):
        radius = outer if i % 2 == 0 else inner
        angle = rotation + i * math.pi / 5
        points.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))
    return points


def make_icon():
    scale = 4
    size = 512 * scale
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Vertical warm gradient inside a rounded square.
    for y in range(size):
        t = y / size
        color = tuple(int(CORAL[i] * (1 - t) + CORAL_DARK[i] * t) for i in range(3))
        draw.line([(0, y), (size, y)], fill=color + (255,))
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    margin = int(size * 0.04)
    mask_draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=int(size * 0.23),
        fill=255,
    )
    img.putalpha(mask)

    overlay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.ellipse(
        [size * 0.58, -size * 0.15, size * 1.18, size * 0.45],
        fill=(255, 255, 255, 28),
    )
    od.ellipse(
        [-size * 0.12, size * 0.68, size * 0.45, size * 1.25],
        fill=(255, 255, 255, 22),
    )
    od.polygon(
        star_points(size * 0.5, size * 0.50, size * 0.30, size * 0.128),
        fill=CREAM + (255,),
    )
    # A little honey dot gives the star a playful highlight.
    od.ellipse(
        [size * 0.68, size * 0.24, size * 0.73, size * 0.29],
        fill=HONEY + (255,),
    )
    img = Image.alpha_composite(img, overlay)
    img = img.resize((512, 512), Image.Resampling.LANCZOS)
    img.save(ASSETS / "icon.png")
    print("wrote", ASSETS / "icon.png")


def make_presplash():
    width, height = 1080, 1920
    img = Image.new("RGB", (width, height), CREAM)
    draw = ImageDraw.Draw(img)
    draw.ellipse([-260, -220, 420, 460], fill=(255, 232, 226))
    draw.ellipse([780, 1420, 1280, 1920], fill=(255, 242, 210))
    draw.polygon(star_points(540, 720, 180, 78), fill=CORAL)
    draw.ellipse([695, 470, 735, 510], fill=HONEY)
    try:
        font = ImageFont.truetype(str(FONT), 76)
        small = ImageFont.truetype(str(FONT), 34)
    except Exception:
        font = ImageFont.load_default()
        small = ImageFont.load_default()
    text = "小星星成长记"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((width - tw) / 2, 1010), text, font=font, fill=INK)
    sub = "把每一个小进步，收进星光里"
    bbox = draw.textbbox((0, 0), sub, font=small)
    sw = bbox[2] - bbox[0]
    draw.text(((width - sw) / 2, 1120), sub, font=small, fill=(149, 141, 159))
    img.save(ASSETS / "presplash.png")
    print("wrote", ASSETS / "presplash.png")


if __name__ == "__main__":
    make_icon()
    make_presplash()
