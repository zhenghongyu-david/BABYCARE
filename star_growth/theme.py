"""Visual language for 小星星成长记.

The palette is intentionally warm and paper-like: cream backgrounds, coral for
actions, honey yellow for stars and a handful of muted accent colours for task
badges.  All sizes are expressed in dp so the UI keeps its proportions on a
phone and in the desktop preview window.
"""
from __future__ import annotations

from kivy.metrics import dp, sp
from kivy.utils import get_color_from_hex


def hex_color(value: str, alpha: float = 1.0):
    color = get_color_from_hex(value)
    if alpha != 1.0:
        color[3] = alpha
    return color


# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------
BG = hex_color("#FFF9F3")
BG_DEEP = hex_color("#FBF1E8")
CARD = hex_color("#FFFFFF")
CARD_SOFT = hex_color("#FFFDF9")
INK = hex_color("#302B38")
INK_SOFT = hex_color("#5E5768")
MUTED = hex_color("#958D9F")
LINE = hex_color("#F1E6DB")

CORAL = hex_color("#FF7A66")
CORAL_DARK = hex_color("#F26350")
CORAL_SOFT = hex_color("#FFE8E2")
CORAL_WASH = hex_color("#FFF3EF")

HONEY = hex_color("#FFC44D")
HONEY_DARK = hex_color("#E8A51D")
HONEY_SOFT = hex_color("#FFF2D2")

MINT = hex_color("#67C4AE")
MINT_DARK = hex_color("#3D9B85")
MINT_SOFT = hex_color("#E2F6F0")
SKY = hex_color("#6FAEE8")
SKY_SOFT = hex_color("#E7F2FD")
LAVENDER = hex_color("#A68BE0")
LAVENDER_SOFT = hex_color("#F0EAFB")
ROSE = hex_color("#EE8FA8")
ROSE_SOFT = hex_color("#FCE8EE")

WHITE = hex_color("#FFFFFF")
BLACK = hex_color("#000000")
OVERLAY = (0.13, 0.10, 0.14, 0.42)

# Accent colours available to a task.  (label, main, wash)
TASK_COLORS = [
    ("珊瑚", "#FF7A66", "#FFE8E2"),
    ("蜂蜜", "#FFC44D", "#FFF2D2"),
    ("薄荷", "#67C4AE", "#E2F6F0"),
    ("天空", "#6FAEE8", "#E7F2FD"),
    ("香芋", "#A68BE0", "#F0EAFB"),
    ("樱花", "#EE8FA8", "#FCE8EE"),
]

TASK_ICONS = ["读", "动", "刷", "收", "睡", "饭", "琴", "花", "画", "星"]

SCHEDULE_LABELS = {
    "daily": "每天",
    "weekdays": "周一到周五",
    "weekend": "周末",
}

# ---------------------------------------------------------------------------
# Type
# ---------------------------------------------------------------------------
FONT_CN = "NotoCN"
FONT_CN_BOLD = "NotoCNBold"
FONT_NUM = "RobotoNumber"

FS_HERO = sp(38)
FS_TITLE = sp(26)
FS_SECTION = sp(18)
FS_BODY = sp(15)
FS_SMALL = sp(12.5)
FS_TINY = sp(11)

# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
PAGE_PAD = dp(20)
CARD_RADIUS = dp(22)
CARD_PAD = dp(18)
GAP = dp(14)
NAV_HEIGHT = dp(76)
MAX_CONTENT_WIDTH = dp(560)


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
