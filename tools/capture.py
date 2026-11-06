"""Capture the app's client area (without the title bar) for visual review."""
from __future__ import annotations

import ctypes
import ctypes.wintypes
import sys
import time
from pathlib import Path

from PIL import ImageGrab

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

user32 = ctypes.windll.user32
TITLE = "小星星成长记"
ROOT = Path(__file__).resolve().parent.parent


def target_pid():
    pid_file = ROOT / ".app_pid"
    if pid_file.exists():
        try:
            return int(pid_file.read_text().strip())
        except ValueError:
            return None
    return None


def find_window():
    wanted = target_pid()
    found = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def callback(hwnd, _lparam):
        length = user32.GetWindowTextLengthW(hwnd)
        if not length or not user32.IsWindowVisible(hwnd):
            return True
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        if TITLE not in buffer.value:
            return True
        pid = ctypes.wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        rect = ctypes.wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        area = max(0, rect.right - rect.left) * max(0, rect.bottom - rect.top)
        found.append((area, hwnd, pid.value))
        return True

    user32.EnumWindows(callback, 0)
    if not found:
        return None
    # The venv launcher may be the recorded PID while the actual SDL window
    # belongs to a child interpreter, so prefer a match but fall back to the
    # largest visible window with our title.
    matching = [item for item in found if wanted and item[2] == wanted]
    selected = max(matching or found)
    print("windows", [(a, h, p) for a, h, p in found], "using", selected[2])
    return selected[1]


def client_rect(hwnd):
    rect = ctypes.wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    point = ctypes.wintypes.POINT(0, 0)
    user32.ClientToScreen(hwnd, ctypes.byref(point))
    return point.x, point.y, point.x + rect.right, point.y + rect.bottom


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "screenshots/window.png")
    hwnd = find_window()
    if not hwnd:
        raise SystemExit("window not found")
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, 9)
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.7)
    bbox = client_rect(hwnd)
    print("client", bbox, "size", bbox[2] - bbox[0], bbox[3] - bbox[1])
    image = ImageGrab.grab(bbox=bbox)
    out.parent.mkdir(parents=True, exist_ok=True)
    image.save(out)
    print("saved", out, image.size)


if __name__ == "__main__":
    main()
