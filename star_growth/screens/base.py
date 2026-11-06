from __future__ import annotations

from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from .. import theme
from ..state import AppState
from ..ui.widgets import StarBadge, TinyButton


class PageScreen(Screen):
    """A scrollable page with a centred, phone-width content column."""

    def __init__(self, app, state: AppState, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.state = state
        self._dirty = True
        self._rebuild_event = None
        with self.canvas.before:
            self._bg_color = Color(*theme.BG)
            self._bg_rect = Rectangle()
        self.bind(pos=self._sync_bg, size=self._sync_bg)
        self.scroll = ScrollView(
            do_scroll_x=False,
            bar_width=dp(2),
            bar_color=theme.CORAL_SOFT,
            bar_inactive_color=theme.CORAL_SOFT,
            scroll_type=["bars", "content"],
        )
        self.content = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=theme.GAP,
        )
        self.content.bind(minimum_height=self.content.setter("height"))
        self.scroll.add_widget(self.content)
        self.add_widget(self.scroll)
        self.bind(width=self._sync_padding)
        self.state.bind(on_change=self._on_state_change)
        Clock.schedule_once(lambda dt: self._first_build(), 0)

    def _first_build(self):
        self._sync_padding()
        self.rebuild()
        self._dirty = False

    def _sync_bg(self, *_):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

    def _sync_padding(self, *_):
        side = max(theme.PAGE_PAD, (self.width - theme.MAX_CONTENT_WIDTH) / 2)
        self.content.padding = [side, dp(8), side, dp(28)]

    def _on_state_change(self, *_):
        self._dirty = True
        if self.manager and self.manager.current == self.name:
            self._schedule_rebuild()

    def _schedule_rebuild(self):
        if self._rebuild_event:
            return
        self._rebuild_event = Clock.schedule_once(self._do_rebuild, 0.02)

    def _do_rebuild(self, *_):
        self._rebuild_event = None
        if not self.manager or self.manager.current != self.name:
            return
        self.rebuild()
        self._dirty = False

    def on_pre_enter(self, *args):
        if self._dirty:
            Clock.schedule_once(lambda dt: self._do_rebuild(), 0)

    def rebuild(self):
        """Override in concrete screens."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Shared page furniture
    # ------------------------------------------------------------------
    def add(self, widget):
        self.content.add_widget(widget)
        return widget

    def add_space(self, height: float):
        spacer = Widget(size_hint_y=None, height=height)
        self.add(spacer)
        return spacer

    def brand_bar(self) -> BoxLayout:
        row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(34),
            spacing=dp(6),
        )
        mark = StarBadge(text="★", font_size=sp(18), color=theme.CORAL, size=(dp(22), dp(22)))
        row.add_widget(mark)
        brand = Label(
            text="小星星成长记",
            font_name=theme.FONT_CN_BOLD,
            font_size=theme.FS_TINY,
            color=theme.MUTED,
            halign="left",
            valign="middle",
            size_hint_x=1,
        )
        brand.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        row.add_widget(brand)
        settings = TinyButton(
            text="设置",
            bg_color=(1, 1, 1, 0),
            text_color=theme.MUTED,
            height=dp(30),
            font_size=theme.FS_TINY,
        )
        settings.bind(on_release=lambda *_: self.app.open_settings())
        row.add_widget(settings)
        return row

    def page_title(self, title: str, subtitle: str = "") -> BoxLayout:
        box = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(4),
        )
        heading = Label(
            text=title,
            font_name=theme.FONT_CN_BOLD,
            font_size=theme.FS_TITLE,
            color=theme.INK,
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(38),
        )
        heading.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        box.add_widget(heading)
        if subtitle:
            sub = Label(
                text=subtitle,
                font_name=theme.FONT_CN,
                font_size=theme.FS_SMALL,
                color=theme.MUTED,
                halign="left",
                valign="middle",
                size_hint_y=None,
                height=dp(22),
            )
            sub.bind(size=lambda inst, val: setattr(inst, "text_size", val))
            box.add_widget(sub)
        box.height = dp(38) + (dp(26) if subtitle else 0)
        return box
