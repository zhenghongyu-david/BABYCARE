from __future__ import annotations

import os
from datetime import date, datetime
from pathlib import Path

from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import FadeTransition, ScreenManager
from kivy.utils import platform

from . import theme
from .fonts import register_fonts
from .photo import pick_image
from .repository import GrowthRepository, RepositoryError
from .screens.album import AlbumScreen
from .screens.points import PointsScreen
from .screens.tasks import TasksScreen
from .screens.today import TodayScreen
from .state import AppState
from .ui.modals import PhotoEditor, PhotoViewer, SettingsSheet, TaskEditor
from .ui.widgets import BottomNav, Toast


class RootWidget(FloatLayout):
    def __init__(self, app: "GrowthApp", state: AppState, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.state = state
        self._toast = None
        self._toast_hide = None
        self._toast_remove = None
        self.main = BoxLayout(orientation="vertical")
        self.add_widget(self.main)
        self.sm = ScreenManager(transition=FadeTransition(duration=0.12))
        self.sm.add_widget(TodayScreen(app=app, state=state, name="today"))
        self.sm.add_widget(TasksScreen(app=app, state=state, name="tasks"))
        self.sm.add_widget(AlbumScreen(app=app, state=state, name="album"))
        self.sm.add_widget(PointsScreen(app=app, state=state, name="stars"))
        self.nav = BottomNav()
        self.nav.on_select = self._select
        self.main.add_widget(self.sm)
        self.main.add_widget(self.nav)
        self.sm.current = "today"
        self.nav.active_name = "today"

    def _select(self, name: str):
        self.app.switch_to(name)

    def show_toast(self, text: str):
        if not text:
            return
        if self._toast is not None:
            Animation.cancel_all(self._toast)
            if self._toast.parent:
                self.remove_widget(self._toast)
            self._toast = None
        if self._toast_hide:
            self._toast_hide.cancel()
            self._toast_hide = None
        if self._toast_remove:
            self._toast_remove.cancel()
            self._toast_remove = None

        toast = Toast(text=text)
        self._toast = toast
        self.add_widget(toast)

        def place(_dt=0):
            toast.pos = (
                (self.width - toast.width) / 2,
                self.nav.height + dp(16),
            )
            toast.opacity = 0
            Animation(opacity=1, d=0.16).start(toast)

        Clock.schedule_once(place, 0)
        self._toast_hide = Clock.schedule_once(self._hide_toast, 2.0)

    def _hide_toast(self, *_):
        if not self._toast:
            return
        toast = self._toast

        def remove(*_):
            if toast.parent:
                self.remove_widget(toast)
            if self._toast is toast:
                self._toast = None

        anim = Animation(opacity=0, d=0.20)
        anim.bind(on_complete=remove)
        anim.start(toast)


class GrowthApp(App):
    name = "stargrowth"
    title = "小星星成长记"

    def build(self):
        register_fonts()
        Window.clearcolor = theme.BG
        Window.softinput_mode = "below_target"
        if platform != "android":
            Window.size = (
                int(os.environ.get("STAR_WINDOW_WIDTH", "360")),
                int(os.environ.get("STAR_WINDOW_HEIGHT", "680")),
            )

        data_dir = os.environ.get("STAR_DATA_DIR")
        if not data_dir:
            data_dir = self.user_data_dir
        self.repo = GrowthRepository(data_dir)
        self.state = AppState(self.repo)
        self._modals = []
        self._last_day = self.state.today
        self._last_hour = datetime.now().hour
        self.icon = str(Path(__file__).resolve().parent.parent / "assets" / "icon.png")
        self.root = RootWidget(app=self, state=self.state)
        return self.root

    def on_start(self):
        Window.bind(on_keyboard=self._on_keyboard)
        Clock.schedule_interval(self._tick, 30)
        Clock.schedule_once(lambda dt: self.root.show_toast("所有记录只保存在这台设备上"), 0.9)

    def on_resume(self):
        self.state.refresh()

    def on_stop(self):
        try:
            self.repo.close()
        except Exception:
            pass

    def _tick(self, *_):
        now = datetime.now()
        if date.today() != self._last_day or now.hour != self._last_hour:
            self._last_day = date.today()
            self._last_hour = now.hour
            self.state.refresh()

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    def switch_to(self, name: str):
        if name not in self.root.sm.screen_names:
            return
        self.root.sm.current = name
        self.root.nav.active_name = name

    def _on_keyboard(self, _window, key, *_args):
        if key == 27:
            if self._modals:
                self._modals[-1].dismiss()
                return True
            if self.root.sm.current != "today":
                self.switch_to("today")
                return True
        return False

    def register_modal(self, modal):
        if modal not in self._modals:
            self._modals.append(modal)

    def forget_modal(self, modal):
        if modal in self._modals:
            self._modals.remove(modal)

    def toast(self, text: str):
        self.root.show_toast(text)

    def _vibrate(self, seconds: float = 0.03):
        if platform != "android":
            return
        try:
            from plyer import vibrator

            vibrator.vibrate(seconds)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Task actions
    # ------------------------------------------------------------------
    def toggle_task(self, task_id: int):
        try:
            result = self.state.toggle_task(int(task_id))
        except RepositoryError as exc:
            self.toast(str(exc))
            return
        if result["done"]:
            self.toast(f"＋{result['points']} 颗星 · {result['title']} 完成啦")
            self._vibrate()
        else:
            self.toast("已取消完成，星星先放回去")

    def open_task_editor(self, task: dict | None = None):
        def save(payload):
            if task:
                self.state.edit_task(int(task["id"]), **payload)
                self.toast("任务已经更新")
            else:
                self.state.add_task(**payload)
                self.toast("新任务已加入今天的清单")
            return True

        def delete(task_id: int):
            self.state.remove_task(int(task_id))
            self.toast("任务已删除")

        TaskEditor(task, on_save=save, on_delete=delete).open()

    # ------------------------------------------------------------------
    # Photos
    # ------------------------------------------------------------------
    def pick_photo(self):
        def selected(path):
            if path:
                self._open_photo_editor(path)

        pick_image(selected)

    def _open_photo_editor(self, path: str):
        def save(source, caption, taken_on):
            self.state.add_photo(source, caption, taken_on)
            self.toast("照片已收进成长相册")
            return True

        PhotoEditor(path, on_save=save).open()

    def open_photo(self, photo: dict):
        path = self.repo.photo_path(photo)
        PhotoViewer(photo, path, on_delete=self._delete_photo).open()

    def _delete_photo(self, photo_id: int):
        self.state.remove_photo(int(photo_id))
        self.toast("照片已删除")

    # ------------------------------------------------------------------
    # Profile
    # ------------------------------------------------------------------
    def open_settings(self):
        SettingsSheet(
            name=self.state.name,
            birthday=self.state.birthday,
            on_save=self._save_profile,
            on_reset=self._reset_all,
        ).open()

    def _save_profile(self, name: str, birthday: str | None):
        self.state.save_profile(name, birthday)
        self.toast("宝贝资料已保存")
        return True

    def _reset_all(self):
        self.state.reset_all()
        self.switch_to("today")
        self.toast("已经清空，重新开始记录吧")
