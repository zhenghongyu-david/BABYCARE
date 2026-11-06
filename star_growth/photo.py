"""Pick an image from the phone gallery (or the desktop file dialog).

Only the selected file's path is returned.  The repository later copies and
re-encodes it into the app's private photo folder, so the diary never depends on
the original file staying in place.
"""
from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path
from typing import Callable
from urllib.parse import unquote, urlparse

from kivy.clock import Clock
from kivy.logger import Logger
from kivy.utils import platform

ImageCallback = Callable[[str | None], None]


def _deliver(callback: ImageCallback, path: str | None, *args):
    def run(_dt):
        callback(path)

    Clock.schedule_once(run, 0)


def _clean_path(path: str | None) -> str | None:
    if not path:
        return None
    path = str(path)
    if path.startswith("file://"):
        parsed = urlparse(path)
        path = unquote(parsed.path)
        if os.name == "nt" and path.startswith("/") and len(path) > 2 and path[2] == ":":
            path = path[1:]
    return path if Path(path).exists() else None


def _copy_android_uri(uri) -> str | None:
    """Copy a content:// image into the app cache and return a real path."""
    from android import mActivity  # type: ignore

    if uri.getScheme() == "file":
        path = uri.getPath()
        return path if path and os.path.exists(path) else None
    resolver = mActivity.getContentResolver()
    mime = resolver.getType(uri) or "image/jpeg"
    extension = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/bmp": ".bmp",
    }.get(mime, ".jpg")
    cache_dir = mActivity.getCacheDir().getAbsolutePath()
    destination = os.path.join(cache_dir, f"picked_{uuid.uuid4().hex[:12]}{extension}")
    pfd = resolver.openFileDescriptor(uri, "r")
    if pfd is None:
        return None
    try:
        source_fd = pfd.getFd()
        with os.fdopen(os.dup(source_fd), "rb") as source:
            with open(destination, "wb") as target:
                shutil.copyfileobj(source, target)
    finally:
        pfd.close()
    return destination if destination and os.path.exists(destination) else None


def _pick_android(callback: ImageCallback):
    try:
        from android import activity, mActivity  # type: ignore
        from jnius import autoclass  # type: ignore

        Intent = autoclass("android.content.Intent")
        Activity = autoclass("android.app.Activity")
        request_code = 0x4152

        def on_activity_result(code, result_code, intent):
            if code != request_code:
                return
            try:
                activity.unbind(on_activity_result=on_activity_result)
            except Exception:
                pass
            if result_code != Activity.RESULT_OK or intent is None:
                _deliver(callback, None)
                return
            uri = intent.getData()
            if uri is None:
                _deliver(callback, None)
                return
            try:
                _deliver(callback, _copy_android_uri(uri))
            except Exception:
                Logger.exception("Photo: could not copy the selected image")
                _deliver(callback, None)

        activity.bind(on_activity_result=on_activity_result)
        intent = Intent(Intent.ACTION_GET_CONTENT)
        intent.setType("image/*")
        intent.addCategory(Intent.CATEGORY_OPENABLE)
        mActivity.startActivityForResult(intent, request_code)
    except Exception:
        Logger.exception("Photo: could not open the Android gallery")
        _deliver(callback, None)


def _pick_windows(callback: ImageCallback):
    """Native Windows file dialog, so the desktop preview needs no Tk."""
    try:
        import ctypes
        import ctypes.wintypes

        class OPENFILENAMEW(ctypes.Structure):
            _fields_ = [
                ("lStructSize", ctypes.wintypes.DWORD),
                ("hwndOwner", ctypes.wintypes.HWND),
                ("hInstance", ctypes.wintypes.HINSTANCE),
                ("lpstrFilter", ctypes.wintypes.LPCWSTR),
                ("lpstrCustomFilter", ctypes.wintypes.LPWSTR),
                ("nMaxCustFilter", ctypes.wintypes.DWORD),
                ("nFilterIndex", ctypes.wintypes.DWORD),
                ("lpstrFile", ctypes.wintypes.LPWSTR),
                ("nMaxFile", ctypes.wintypes.DWORD),
                ("lpstrFileTitle", ctypes.wintypes.LPWSTR),
                ("nMaxFileTitle", ctypes.wintypes.DWORD),
                ("lpstrInitialDir", ctypes.wintypes.LPCWSTR),
                ("lpstrTitle", ctypes.wintypes.LPCWSTR),
                ("Flags", ctypes.wintypes.DWORD),
                ("nFileOffset", ctypes.wintypes.WORD),
                ("nFileExtension", ctypes.wintypes.WORD),
                ("lpstrDefExt", ctypes.wintypes.LPCWSTR),
                ("lCustData", ctypes.wintypes.LPARAM),
                ("lpfnHook", ctypes.c_void_p),
                ("lpTemplateName", ctypes.wintypes.LPCWSTR),
                ("pvReserved", ctypes.c_void_p),
                ("dwReserved", ctypes.wintypes.DWORD),
                ("FlagsEx", ctypes.wintypes.DWORD),
            ]

        buffer = ctypes.create_unicode_buffer(32768)
        filters = ctypes.create_unicode_buffer(
            "图片\0*.jpg;*.jpeg;*.png;*.webp;*.bmp\0所有文件\0*.*\0\0"
        )
        dialog = OPENFILENAMEW()
        dialog.lStructSize = ctypes.sizeof(OPENFILENAMEW)
        dialog.hwndOwner = ctypes.windll.user32.GetForegroundWindow()
        dialog.lpstrFilter = ctypes.cast(filters, ctypes.wintypes.LPCWSTR)
        dialog.lpstrFile = ctypes.cast(buffer, ctypes.wintypes.LPWSTR)
        dialog.nMaxFile = len(buffer)
        dialog.lpstrTitle = "选择一张照片"
        dialog.Flags = 0x00001000 | 0x00000800 | 0x00000008  # file/path must exist, no dir change
        if ctypes.windll.comdlg32.GetOpenFileNameW(ctypes.byref(dialog)):
            path = buffer.value
        else:
            path = None
    except Exception:
        path = None
    _deliver(callback, _clean_path(path))


def _pick_desktop(callback: ImageCallback):
    if platform == "win":
        _pick_windows(callback)
        return
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        path = filedialog.askopenfilename(
            title="选择一张照片",
            filetypes=[
                ("图片", "*.jpg *.jpeg *.png *.webp *.bmp"),
                ("所有文件", "*.*"),
            ],
        )
        root.destroy()
    except Exception:
        path = None
    _deliver(callback, _clean_path(path))


def pick_image(callback: ImageCallback):
    if platform == "android":
        _pick_android(callback)
    else:
        _pick_desktop(callback)
