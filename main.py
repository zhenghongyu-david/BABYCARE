"""小星星成长记 - local-first growth diary.

Run from this directory with:

    python main.py

The Android build uses this file as its entry point; see README.md and
buildozer.spec.
"""
from __future__ import annotations

import ctypes
import os
import sys

os.environ.setdefault("KIVY_NO_ARGS", "1")
if sys.platform == "win32":
    # Use a crisp 1x mobile preview window on Windows instead of inheriting
    # the desktop's 150% scaling.  Android ignores these variables.
    os.environ.setdefault("KIVY_METRICS_DENSITY", "1")
    os.environ.setdefault("KIVY_DPI", "96")
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass

from kivy.config import Config  # noqa: E402

Config.set("graphics", "width", os.environ.get("STAR_WINDOW_WIDTH", "360"))
Config.set("graphics", "height", os.environ.get("STAR_WINDOW_HEIGHT", "680"))
Config.set("graphics", "resizable", "1")
Config.set("graphics", "multisamples", "2")
Config.set("input", "mouse", "mouse,multitouch_on_demand")
Config.set("kivy", "exit_on_escape", "0")

from star_growth.app import GrowthApp  # noqa: E402


if __name__ == "__main__":
    GrowthApp().run()
