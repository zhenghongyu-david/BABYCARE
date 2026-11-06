"""Click a point in the app's client area (physical pixels, origin top-left)."""
from __future__ import annotations

import ctypes
import ctypes.wintypes
import sys
import time
from pathlib import Path

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

user32 = ctypes.windll.user32
TITLE = "小星星成长记"
ROOT = Path(__file__).resolve().parent.parent


def find_window():
    pid_file = ROOT / ".app_pid"
    wanted = int(pid_file.read_text().strip()) if pid_file.exists() else None
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
        found.append((pid.value, hwnd))
        return True

    user32.EnumWindows(callback, 0)
    if not found:
        return None
    matching = [item for item in found if wanted and item[0] == wanted]
    return (matching or found)[0][1]


def main():
    x, y = int(sys.argv[1]), int(sys.argv[2])
    hwnd = find_window()
    if not hwnd:
        raise SystemExit("window not found")
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, 9)
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.4)
    point = ctypes.wintypes.POINT(0, 0)
    user32.ClientToScreen(hwnd, ctypes.byref(point))
    user32.SetCursorPos(point.x + x, point.y + y)
    user32.mouse_event(0x0002, 0, 0, 0, 0)
    time.sleep(0.06)
    user32.mouse_event(0x0004, 0, 0, 0, 0)
    time.sleep(0.3)
    print("clicked", point.x + x, point.y + y)


if __name__ == "__main__":
    main()
