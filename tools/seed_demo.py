"""Build a small, local-only demo library for screenshots and manual review."""
from __future__ import annotations

import math
import random
import sys
from datetime import date, timedelta
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from star_growth.repository import GrowthRepository  # noqa: E402

DATA = ROOT / "demo_data"
ART = ROOT / "demo_art"


def gradient(size, top, bottom):
    img = Image.new("RGB", size, top)
    draw = ImageDraw.Draw(img)
    for y in range(size[1]):
        t = y / max(1, size[1] - 1)
        color = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
        draw.line([(0, y), (size[0], y)], fill=color)
    return img


def park():
    img = gradient((900, 900), (182, 220, 241), (245, 231, 199))
    d = ImageDraw.Draw(img)
    d.ellipse((620, 90, 760, 230), fill=(255, 205, 111))
    d.ellipse((90, 130, 300, 220), fill=(255, 255, 255))
    d.ellipse((190, 100, 390, 220), fill=(255, 255, 255))
    d.ellipse((-160, 520, 620, 980), fill=(143, 192, 128))
    d.ellipse((380, 560, 1080, 1040), fill=(116, 172, 111))
    d.rectangle((0, 740, 900, 900), fill=(158, 196, 126))
    # tree
    d.rectangle((160, 470, 205, 760), fill=(139, 100, 67))
    for cx, cy, r in [(120, 460, 90), (210, 440, 105), (265, 500, 75)]:
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(91, 157, 101))
    # kite
    d.line((620, 350, 710, 590), fill=(90, 78, 80), width=3)
    d.polygon([(620, 300), (680, 360), (620, 430), (560, 360)], fill=(255, 122, 102))
    d.line((620, 300, 620, 430), fill=(255, 240, 220), width=3)
    d.line((560, 360, 680, 360), fill=(255, 240, 220), width=3)
    # flowers
    for _ in range(16):
        x = random.randint(20, 860)
        y = random.randint(760, 880)
        d.ellipse((x, y, x + 9, y + 9), fill=random.choice([(255, 255, 255), (255, 213, 92), (242, 143, 168)]))
    return img


def blocks():
    img = gradient((900, 900), (255, 239, 222), (255, 249, 243))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 720, 900, 900), fill=(238, 210, 181))
    palette = [(255, 122, 102), (255, 196, 77), (103, 196, 174), (111, 174, 232), (166, 139, 224)]
    blocks_data = [
        (300, 650, 300, 140, 0),
        (320, 740, 260, 100, 1),
        (580, 680, 160, 160, 2),
        (200, 500, 180, 150, 3),
        (430, 520, 220, 120, 4),
    ]
    for x, y, w, h, ci in blocks_data:
        color = palette[ci]
        d.rounded_rectangle((x, y - h, x + w, y), radius=18, fill=color)
        d.rounded_rectangle((x + 12, y - h + 12, x + w - 12, y - 12), radius=12, outline=(255, 255, 255), width=5)
        for dot in range(3):
            d.ellipse((x + 30 + dot * 35, y - h / 2 - 8, x + 44 + dot * 35, y - h / 2 + 6), fill=(255, 255, 255, 180))
    return img


def drawing():
    img = gradient((900, 900), (255, 248, 235), (252, 232, 215))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((70, 70, 830, 830), radius=8, fill=(255, 253, 246), outline=(235, 216, 197), width=3)
    d.ellipse((320, 180, 580, 440), fill=(255, 196, 77))
    for i in range(12):
        angle = i * math.pi / 6
        x1, y1 = 450 + math.cos(angle) * 150, 310 + math.sin(angle) * 150
        x2, y2 = 450 + math.cos(angle) * 195, 310 + math.sin(angle) * 195
        d.line((x1, y1, x2, y2), fill=(255, 168, 72), width=10)
    d.arc((180, 300, 720, 780), 200, 340, fill=(255, 122, 102), width=18)
    d.arc((180, 300, 720, 780), 200, 340, fill=(255, 196, 77), width=12)
    for x, y, c in [(250, 550, (103, 196, 174)), (610, 560, (111, 174, 232))]:
        for i in range(5):
            angle = i * 2 * math.pi / 5
            px, py = x + math.cos(angle) * 34, y + math.sin(angle) * 34
            d.ellipse((px - 22, py - 22, px + 22, py + 22), fill=c)
        d.ellipse((x - 18, y - 18, x + 18, y + 18), fill=(255, 220, 120))
    return img


def leaves():
    img = gradient((900, 900), (255, 224, 190), (241, 197, 155))
    random.seed(7)
    colors = [(230, 135, 87), (217, 110, 77), (247, 179, 85), (183, 126, 72), (248, 208, 129)]
    for i in range(26):
        x = random.randint(-60, 900)
        y = random.randint(-40, 850)
        w = random.randint(55, 130)
        h = random.randint(25, 60)
        angle = random.randint(0, 359)
        leaf = Image.new("RGBA", (w + 20, h + 20), (0, 0, 0, 0))
        ld = ImageDraw.Draw(leaf)
        ld.ellipse((10, 10, w + 10, h + 10), fill=random.choice(colors) + (235,))
        ld.line((20, (h + 20) / 2, w, (h + 20) / 2), fill=(130, 80, 50, 160), width=2)
        leaf = leaf.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
        img.paste(leaf, (x, y), leaf)
    return img


def cake():
    img = gradient((900, 900), (255, 240, 226), (250, 216, 204))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 760, 900, 900), fill=(239, 214, 190))
    d.rounded_rectangle((250, 460, 650, 760), radius=24, fill=(255, 249, 238))
    d.rectangle((250, 540, 650, 610), fill=(255, 122, 102))
    for x in range(280, 650, 55):
        d.ellipse((x, 440, x + 28, 480), fill=(255, 122, 102))
    for x in [350, 450, 550]:
        d.rectangle((x, 340, x + 10, 445), fill=(255, 196, 77))
        d.ellipse((x - 6, 318, x + 16, 342), fill=(255, 196, 77))
    d.text((360, 800), "", fill=(0, 0, 0))
    return img


def main():
    DATA.mkdir(exist_ok=True)
    ART.mkdir(exist_ok=True)
    repo = GrowthRepository(DATA)
    repo.reset_all()
    repo.update_profile("小满", "2021-03-18")
    repo.create_task("给小花浇水", 1, "花", "#EE8FA8", "daily")
    repo.create_task("练琴 15 分钟", 3, "琴", "#A68BE0", "daily")
    tasks = repo.list_tasks()
    today = date.today()
    # A believable day: three done, three waiting.
    for task in tasks[:3]:
        repo.toggle_completion(task["id"], today.isoformat())
    for task in tasks[:2]:
        repo.toggle_completion(task["id"], (today - timedelta(days=1)).isoformat())
    for task in tasks[:1]:
        repo.toggle_completion(task["id"], (today - timedelta(days=2)).isoformat())

    makers = [park, blocks, drawing, leaves, cake]
    captions = [
        "公园里的下午，风筝飞得好高",
        "自己搭了一座很高的塔",
        "今天画了一个小太阳",
        "捡到一把秋天的颜色",
        "第一次帮忙做蛋糕",
    ]
    dates = [today, today - timedelta(days=3), today - timedelta(days=9), today - timedelta(days=18), today - timedelta(days=32)]
    for index, (maker, caption, day) in enumerate(zip(makers, captions, dates)):
        path = ART / f"demo_{index}.png"
        maker().save(path)
        repo.add_photo(path, caption, day.isoformat())

    print("profile:", repo.get_profile())
    print("tasks:", len(repo.list_tasks()))
    print("points:", repo.total_points(), "today:", repo.points_on(today.isoformat()))
    print("photos:", repo.photo_count())
    repo.close()


if __name__ == "__main__":
    main()
