"""Hand-built Kivy widgets.

Kivy ships with functional but visually generic widgets.  The diary uses a
small set of rounded, paper-like primitives instead, so the whole app keeps one
calm visual rhythm on a phone screen.
"""
from __future__ import annotations

from typing import Callable

from kivy.graphics import Color, Ellipse, Line, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.properties import (
    BooleanProperty,
    ListProperty,
    NumericProperty,
    ObjectProperty,
    StringProperty,
)
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget

from .. import theme
from ..state import WEEKDAY_CN
from ..theme import FONT_CN


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def rgba(color, alpha: float | None = None):
    values = list(color)
    if len(values) == 3:
        values.append(1.0)
    if alpha is not None:
        values[3] = alpha
    return values


class Card(BoxLayout):
    """A rounded white panel with a soft drop shadow."""

    bg_color = ListProperty(theme.CARD)
    radius = NumericProperty(theme.CARD_RADIUS)
    shadow = BooleanProperty(True)
    border = BooleanProperty(False)

    def __init__(self, **kwargs):
        kwargs.setdefault("orientation", "vertical")
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0, 0, 0, 0.045 if self.shadow else 0)
            self._shadow = RoundedRectangle()
            self._bg_color = Color(*rgba(self.bg_color))
            self._bg = RoundedRectangle()
            self._border_color = Color(*theme.LINE)
            self._border = Line(width=1)
        self.bind(
            pos=self._sync_canvas,
            size=self._sync_canvas,
            bg_color=self._sync_color,
            radius=self._sync_radius,
        )
        self._sync_canvas()
        self._sync_color()

    def _sync_canvas(self, *_):
        x, y = self.pos
        w, h = self.size
        r = max(0, self.radius)
        if self.shadow:
            self._shadow.pos = (x, y - dp(3))
            self._shadow.size = (w, h)
            self._shadow.radius = [r]
        else:
            self._shadow.size = (0, 0)
        self._bg.pos = (x, y)
        self._bg.size = (w, h)
        self._bg.radius = [r]
        self._border.rounded_rectangle = (x, y, w, h, r)
        self._border_color.a = 1 if self.border else 0

    def _sync_color(self, *_):
        self._bg_color.rgba = rgba(self.bg_color)

    def _sync_radius(self, *_):
        self._bg.radius = [max(0, self.radius)]
        self._shadow.radius = [max(0, self.radius)]
        self._border.rounded_rectangle = (
            self.x,
            self.y,
            self.width,
            self.height,
            max(0, self.radius),
        )


class WrappedLabel(Label):
    """A label that grows vertically to fit wrapped text."""

    def __init__(self, **kwargs):
        kwargs.setdefault("font_name", FONT_CN)
        kwargs.setdefault("font_size", theme.FS_BODY)
        kwargs.setdefault("color", theme.INK)
        kwargs.setdefault("halign", "left")
        kwargs.setdefault("valign", "top")
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("line_height", 1.22)
        super().__init__(**kwargs)
        self.bind(width=self._resize_text, texture_size=self._resize_height)
        self._resize_text()

    def _resize_text(self, *_):
        self.text_size = (max(1, self.width), None)

    def _resize_height(self, *_):
        self.height = max(dp(16), self.texture_size[1])


class TitleLabel(WrappedLabel):
    def __init__(self, **kwargs):
        kwargs.setdefault("font_name", theme.FONT_CN_BOLD)
        kwargs.setdefault("font_size", theme.FS_TITLE)
        kwargs.setdefault("color", theme.INK)
        kwargs.setdefault("line_height", 1.08)
        super().__init__(**kwargs)


class SectionTitle(BoxLayout):
    """Section heading with an optional text action on the right."""

    def __init__(self, title: str, action: str = "", on_action: Callable | None = None, **kwargs):
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(28))
        kwargs.setdefault("spacing", dp(8))
        super().__init__(**kwargs)
        heading = Label(
            text=title,
            font_name=theme.FONT_CN_BOLD,
            font_size=theme.FS_SECTION,
            color=theme.INK,
            halign="left",
            valign="middle",
            size_hint_x=1,
        )
        heading.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        self.add_widget(heading)
        if action:
            button = TinyButton(
                text=action,
                bg_color=(1, 1, 1, 0),
                text_color=theme.CORAL_DARK,
                height=dp(28),
                font_size=theme.FS_SMALL,
                on_release=lambda *_: on_action() if on_action else None,
            )
            self.add_widget(button)


class Pill(Label):
    bg_color = ListProperty(theme.CORAL_SOFT)

    def __init__(self, **kwargs):
        kwargs["bg_color"] = kwargs.pop("bg_color", theme.CORAL_SOFT)
        kwargs.setdefault("font_name", FONT_CN)
        kwargs.setdefault("font_size", theme.FS_TINY)
        kwargs.setdefault("color", theme.CORAL_DARK)
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("height", dp(24))
        kwargs.setdefault("halign", "center")
        kwargs.setdefault("valign", "middle")
        self._radius = kwargs.pop("radius", dp(12))
        super().__init__(**kwargs)
        with self.canvas.before:
            self._color = Color(*rgba(self.bg_color))
            self._rect = RoundedRectangle(radius=[self._radius])
        self.bind(
            pos=self._sync,
            size=self._sync,
            texture_size=self._sync_size,
            bg_color=self._sync_color,
        )
        self._sync_size()

    def _sync_size(self, *_):
        self.width = max(dp(34), self.texture_size[0] + dp(20))
        self._sync()

    def _sync(self, *_):
        self._rect.pos = self.pos
        self._rect.size = self.size
        self._rect.radius = [self._radius]

    def _sync_color(self, *_):
        self._color.rgba = rgba(self.bg_color)


class TinyButton(ButtonBehavior, Label):
    def __init__(self, **kwargs):
        bg = kwargs.pop("bg_color", theme.CORAL_SOFT)
        text_color = kwargs.pop("text_color", theme.CORAL_DARK)
        self._base_bg = rgba(bg)
        self._base_text = rgba(text_color)
        kwargs.setdefault("font_name", FONT_CN)
        kwargs.setdefault("font_size", theme.FS_SMALL)
        kwargs.setdefault("color", text_color)
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("height", dp(32))
        kwargs.setdefault("halign", "center")
        kwargs.setdefault("valign", "middle")
        self._radius = kwargs.pop("radius", dp(11))
        super().__init__(**kwargs)
        with self.canvas.before:
            self._color = Color(*self._base_bg)
            self._rect = RoundedRectangle(radius=[self._radius])
        self.bind(
            pos=self._sync,
            size=self._sync,
            texture_size=self._sync_size,
            state=self._on_state,
            disabled=self._on_disabled,
        )
        self._sync_size()

    def _sync_size(self, *_):
        self.width = max(dp(38), self.texture_size[0] + dp(22))
        self._sync()

    def _sync(self, *_):
        self._rect.pos = self.pos
        self._rect.size = self.size
        self._rect.radius = [self._radius]

    def _on_state(self, *_):
        if self.state == "down":
            self._color.rgba = (0.6, 0.5, 0.45, 0.16) if self._base_bg[3] == 0 else (
                max(0, self._base_bg[0] - 0.05),
                max(0, self._base_bg[1] - 0.05),
                max(0, self._base_bg[2] - 0.05),
                self._base_bg[3],
            )
        else:
            self._color.rgba = self._base_bg

    def _on_disabled(self, *_):
        self.opacity = 0.45 if self.disabled else 1


class PrimaryButton(ButtonBehavior, Label):
    def __init__(self, **kwargs):
        bg = kwargs.pop("bg_color", theme.CORAL)
        self._base_bg = rgba(bg)
        self._base_text = rgba(kwargs.pop("text_color", theme.WHITE))
        kwargs.setdefault("font_name", theme.FONT_CN_BOLD)
        kwargs.setdefault("font_size", theme.FS_BODY)
        kwargs.setdefault("color", self._base_text)
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(52))
        kwargs.setdefault("halign", "center")
        kwargs.setdefault("valign", "middle")
        self._radius = kwargs.pop("radius", dp(16))
        super().__init__(**kwargs)
        with self.canvas.before:
            self._color = Color(*self._base_bg)
            self._rect = RoundedRectangle(radius=[self._radius])
        self.bind(
            pos=self._sync,
            size=self._sync,
            state=self._on_state,
            disabled=self._on_disabled,
        )

    def _sync(self, *_):
        self._rect.pos = self.pos
        self._rect.size = self.size
        self._rect.radius = [self._radius]

    def _on_state(self, *_):
        if self.state == "down":
            self._color.rgba = (
                max(0, self._base_bg[0] - 0.08),
                max(0, self._base_bg[1] - 0.08),
                max(0, self._base_bg[2] - 0.05),
                1,
            )
        else:
            self._color.rgba = self._base_bg

    def _on_disabled(self, *_):
        self.opacity = 0.45 if self.disabled else 1


class Bubble(Label):
    """A round task icon with a Chinese character."""

    bubble_color = ListProperty(theme.CORAL)

    def __init__(self, **kwargs):
        kwargs.setdefault("bubble_color", kwargs.pop("bg_color", theme.CORAL))
        kwargs.setdefault("font_name", theme.FONT_CN_BOLD)
        kwargs.setdefault("font_size", sp(19))
        kwargs.setdefault("color", theme.WHITE)
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("size", (dp(44), dp(44)))
        kwargs.setdefault("halign", "center")
        kwargs.setdefault("valign", "middle")
        super().__init__(**kwargs)
        with self.canvas.before:
            self._color = Color(*rgba(self.bubble_color))
            self._circle = Ellipse()
        self.bind(pos=self._sync, size=self._sync, bubble_color=self._sync)

    def _sync(self, *_):
        self._circle.pos = self.pos
        self._circle.size = self.size
        self._color.rgba = rgba(self.bubble_color)


class StarBadge(Label):
    def __init__(self, **kwargs):
        kwargs.setdefault("text", "★")
        kwargs.setdefault("font_name", FONT_CN)
        kwargs.setdefault("font_size", sp(23))
        kwargs.setdefault("color", theme.HONEY)
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("size", (dp(28), dp(28)))
        kwargs.setdefault("halign", "center")
        kwargs.setdefault("valign", "middle")
        super().__init__(**kwargs)


class CheckMark(Widget):
    """Visual completion mark.  A whole task row is the touch target."""

    done = BooleanProperty(False)
    accent = ListProperty(theme.CORAL)

    def __init__(self, **kwargs):
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("size", (dp(32), dp(32)))
        super().__init__(**kwargs)
        self.bind(pos=self._redraw, size=self._redraw, done=self._redraw, accent=self._redraw)
        self._redraw()

    def _redraw(self, *_):
        self.canvas.clear()
        x, y = self.pos
        w, h = self.size
        side = min(w, h)
        pad = dp(2)
        cx, cy = x + w / 2, y + h / 2
        r = side / 2 - pad
        with self.canvas:
            if self.done:
                Color(*rgba(self.accent))
                Ellipse(pos=(cx - r, cy - r), size=(r * 2, r * 2))
                Color(1, 1, 1, 1)
                Line(
                    points=[
                        cx - r * 0.42,
                        cy + r * 0.02,
                        cx - r * 0.12,
                        cy - r * 0.30,
                        cx + r * 0.45,
                        cy + r * 0.34,
                    ],
                    width=dp(2.1),
                    cap="round",
                    joint="round",
                )
            else:
                Color(1, 1, 1, 1)
                Ellipse(pos=(cx - r, cy - r), size=(r * 2, r * 2))
                Color(*theme.hex_color("#D9CDC2"))
                Line(circle=(cx, cy, r), width=dp(1.8))


class InitialAvatar(FloatLayout):
    name = StringProperty("小宝贝")
    diameter = NumericProperty(dp(52))

    def __init__(self, **kwargs):
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("size", (dp(52), dp(52)))
        super().__init__(**kwargs)
        self.size = (self.diameter, self.diameter)
        with self.canvas.before:
            self._ring_color = Color(1, 1, 1, 0.9)
            self._ring = Ellipse()
            self._fill_color = Color(*theme.CORAL_SOFT)
            self._fill = Ellipse()
        self._label = Label(
            text="宝",
            font_name=theme.FONT_CN_BOLD,
            font_size=sp(20),
            color=theme.CORAL_DARK,
            halign="center",
            valign="middle",
        )
        self.add_widget(self._label)
        self.bind(pos=self._sync, size=self._sync, name=self._sync_name, diameter=self._sync_size)
        self._sync_name()

    def _sync_size(self, *_):
        self.size = (self.diameter, self.diameter)

    def _sync_name(self, *_):
        name = (self.name or "宝").strip()
        self._label.text = name[0] if name else "宝"

    def _sync(self, *_):
        x, y = self.pos
        w, h = self.size
        pad = dp(2)
        self._ring.pos = (x, y)
        self._ring.size = (w, h)
        self._fill.pos = (x + pad, y + pad)
        self._fill.size = (w - pad * 2, h - pad * 2)
        self._label.pos = self.pos
        self._label.size = self.size


class ProgressRing(FloatLayout):
    progress = NumericProperty(0.0)
    track_color = ListProperty((1, 1, 1, 0.22))
    bar_color = ListProperty(theme.WHITE)
    line_width = NumericProperty(dp(8))

    def __init__(self, **kwargs):
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("size", (dp(98), dp(98)))
        super().__init__(**kwargs)
        with self.canvas:
            self._disc_color = Color(1, 1, 1, 0.10)
            self._disc = Ellipse()
            self._track_color = Color(*self.track_color)
            self._track = Line(width=self.line_width)
            self._bar_color = Color(*self.bar_color)
            self._bar = Line(width=self.line_width)
        self.bind(
            pos=self._redraw,
            size=self._redraw,
            progress=self._redraw,
            line_width=self._redraw,
            track_color=self._sync_colors,
            bar_color=self._sync_colors,
        )
        self._redraw()

    def _sync_colors(self, *_):
        self._track_color.rgba = rgba(self.track_color)
        self._bar_color.rgba = rgba(self.bar_color)

    def _redraw(self, *_):
        x, y = self.pos
        w, h = self.size
        cx, cy = x + w / 2, y + h / 2
        r = min(w, h) / 2 - self.line_width / 2 - dp(3)
        self._disc.pos = (cx - r, cy - r)
        self._disc.size = (r * 2, r * 2)
        self._track.circle = (cx, cy, r)
        p = max(0.0, min(1.0, self.progress))
        if p <= 0:
            self._bar.circle = (cx, cy, r, 0, 0)
        else:
            self._bar.circle = (cx, cy, r, 90, 90 - 360 * p)
        self._sync_colors()


class WeekChart(BoxLayout):
    """A tiny seven-day bar chart made of real widgets."""

    values = ListProperty([])
    labels = ListProperty([])
    today_index = NumericProperty(-1)

    def __init__(self, **kwargs):
        kwargs.setdefault("orientation", "horizontal")
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(150))
        kwargs.setdefault("spacing", dp(5))
        super().__init__(**kwargs)
        self.bind(values=self._rebuild, labels=self._rebuild, today_index=self._rebuild)
        self._rebuild()

    def _rebuild(self, *_):
        self.clear_widgets()
        values = [int(v) for v in self.values] or [0] * 7
        labels = list(self.labels) or WEEKDAY_CN
        top = max(values + [1])
        for index in range(7):
            value = values[index] if index < len(values) else 0
            label = labels[index] if index < len(labels) else WEEKDAY_CN[index % 7]
            column = BoxLayout(orientation="vertical", spacing=dp(4))
            number = Label(
                text=str(value) if value else "",
                font_name=theme.FONT_CN,
                font_size=theme.FS_TINY,
                color=theme.CORAL_DARK if index == self.today_index else theme.MUTED,
                size_hint_y=None,
                height=dp(18),
            )
            column.add_widget(number)
            column.add_widget(_Bar(value=value, top=top, highlight=index == self.today_index))
            day = Label(
                text=label,
                font_name=theme.FONT_CN_BOLD if index == self.today_index else theme.FONT_CN,
                font_size=theme.FS_TINY,
                color=theme.INK if index == self.today_index else theme.MUTED,
                size_hint_y=None,
                height=dp(22),
            )
            column.add_widget(day)
            self.add_widget(column)


class _Bar(Widget):
    def __init__(self, value: int, top: int, highlight: bool, **kwargs):
        super().__init__(**kwargs)
        self.value = value
        self.max_value = max(1, top)
        self.highlight = highlight
        with self.canvas:
            self._track_color = Color(*rgba(theme.CORAL_WASH))
            self._track = RoundedRectangle(radius=[dp(7)])
            self._fill_color = Color(*(theme.CORAL if highlight else theme.HONEY))
            self._fill = RoundedRectangle(radius=[dp(7)])
        self.bind(pos=self._sync, size=self._sync)
        self._sync()

    def _sync(self, *_):
        x, y = self.pos
        w, h = self.size
        pad = dp(4)
        bar_w = min(dp(18), w - pad * 2)
        bx = x + (w - bar_w) / 2
        self._track.pos = (bx, y)
        self._track.size = (bar_w, h)
        ratio = max(0.06, min(1.0, self.value / self.max_value))
        fh = (h - dp(2)) * ratio
        self._fill.pos = (bx, y + dp(1))
        self._fill.size = (bar_w, fh)
        self._track.radius = [dp(7)]
        self._fill.radius = [dp(7)]


class NavItem(ButtonBehavior, BoxLayout):
    active = BooleanProperty(False)
    label = StringProperty("")
    name = StringProperty("")

    def __init__(self, **kwargs):
        kwargs.setdefault("orientation", "vertical")
        kwargs.setdefault("padding", [dp(8), dp(6)])
        super().__init__(**kwargs)
        self._label = Label(
            text=self.label,
            font_name=theme.FONT_CN,
            font_size=theme.FS_SMALL,
            color=theme.MUTED,
            size_hint_y=1,
            halign="center",
            valign="middle",
        )
        self.add_widget(self._label)
        with self.canvas.before:
            self._pill_color = Color(*theme.CORAL_SOFT)
            self._pill = RoundedRectangle(radius=[dp(17)])
        self.bind(
            active=self._sync_state,
            label=self._sync_label,
            pos=self._sync_pill,
            size=self._sync_pill,
        )
        self._sync_state()
        self._sync_pill()

    def _sync_label(self, *_):
        self._label.text = self.label

    def _sync_state(self, *_):
        self._label.color = theme.CORAL_DARK if self.active else theme.MUTED
        self._label.font_name = theme.FONT_CN_BOLD if self.active else theme.FONT_CN
        self._pill_color.a = 1 if self.active else 0
        self._sync_pill()

    def _sync_pill(self, *_):
        self._pill.pos = (self.x, self.y + (self.height - dp(38)) / 2)
        self._pill.size = (self.width, dp(38))
        self._pill.radius = [dp(17)]


class BottomNav(BoxLayout):
    active_name = StringProperty("today")
    on_select = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        kwargs.setdefault("orientation", "horizontal")
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", theme.NAV_HEIGHT)
        kwargs.setdefault("padding", [dp(10), dp(6), dp(10), dp(8)])
        super().__init__(**kwargs)
        self._items: dict[str, NavItem] = {}
        entries = [
            ("today", "今日"),
            ("tasks", "任务"),
            ("album", "相册"),
            ("stars", "星星"),
        ]
        for name, text in entries:
            item = NavItem(label=text, name=name)
            item.bind(on_release=lambda inst: self._choose(inst.name))
            self._items[name] = item
            self.add_widget(item)
        with self.canvas.before:
            self._bg_color = Color(*theme.CARD)
            self._bg = RoundedRectangle(radius=[0, 0, 0, 0])
            self._line_color = Color(*theme.LINE)
            self._line = Line(width=1)
            self._shadow_color = Color(0, 0, 0, 0.035)
            self._shadow = RoundedRectangle()
        self.bind(pos=self._sync, size=self._sync, active_name=self._sync_active)
        self._sync_active()
        self._sync()

    def _sync(self, *_):
        x, y = self.pos
        w, h = self.size
        self._bg.pos = (x, y)
        self._bg.size = (w, h)
        self._line.points = [x, y + h, x + w, y + h]
        self._shadow.pos = (x, y + h)
        self._shadow.size = (w, dp(6))

    def _sync_active(self, *_):
        for name, item in self._items.items():
            item.active = name == self.active_name

    def _choose(self, name: str):
        if self.on_select:
            self.on_select(name)


class Toast(Label):
    def __init__(self, **kwargs):
        kwargs.setdefault("font_name", theme.FONT_CN)
        kwargs.setdefault("font_size", theme.FS_SMALL)
        kwargs.setdefault("color", theme.WHITE)
        kwargs.setdefault("halign", "center")
        kwargs.setdefault("valign", "middle")
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("height", dp(40))
        super().__init__(**kwargs)
        self.opacity = 0
        with self.canvas.before:
            self._color = Color(0.20, 0.17, 0.22, 0.94)
            self._rect = RoundedRectangle(radius=[dp(14)])
        self.bind(pos=self._sync, size=self._sync, texture_size=self._sync_size)
        self._sync_size()

    def _sync_size(self, *_):
        self.width = min(dp(330), self.texture_size[0] + dp(34))
        self._sync()

    def _sync(self, *_):
        self._rect.pos = self.pos
        self._rect.size = self.size


class PhotoCard(ButtonBehavior, Card):
    photo = ObjectProperty(None, allownone=True)
    thumb_path = StringProperty("")
    caption = StringProperty("")
    date_text = StringProperty("")

    def __init__(self, **kwargs):
        kwargs.setdefault("orientation", "vertical")
        kwargs.setdefault("padding", dp(8))
        kwargs.setdefault("spacing", dp(7))
        kwargs.setdefault("bg_color", theme.CARD)
        kwargs.setdefault("radius", dp(18))
        super().__init__(**kwargs)
        self._image = _PhotoImage()
        self.add_widget(self._image)
        self._caption = Label(
            text=self.caption or "这一刻",
            font_name=theme.FONT_CN,
            font_size=theme.FS_SMALL,
            color=theme.INK,
            size_hint_y=None,
            height=dp(22),
            halign="left",
            valign="middle",
            shorten=True,
            shorten_from="right",
        )
        self._caption.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        self.add_widget(self._caption)
        self._date = Label(
            text=self.date_text,
            font_name=theme.FONT_CN,
            font_size=theme.FS_TINY,
            color=theme.MUTED,
            size_hint_y=None,
            height=dp(16),
            halign="left",
            valign="middle",
        )
        self._date.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        self.add_widget(self._date)
        self.bind(
            thumb_path=self._apply_image,
            caption=self._apply_caption,
            date_text=self._apply_date,
        )
        self._apply_image()
        self._apply_caption()
        self._apply_date()

    def _apply_image(self, *_):
        self._image.source = self.thumb_path

    def _apply_caption(self, *_):
        self._caption.text = self.caption or "这一刻"

    def _apply_date(self, *_):
        self._date.text = self.date_text


class _PhotoImage(Widget):
    source = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._texture = None
        self._image = None
        from kivy.uix.image import Image

        self._image = Image(
            source="",
            fit_mode="cover",
            mipmap=True,
        )
        self.add_widget(self._image)
        self.bind(pos=self._sync, size=self._sync, source=self._apply)

    def _apply(self, *_):
        if self._image:
            self._image.source = self.source

    def _sync(self, *_):
        if self._image:
            self._image.pos = self.pos
            self._image.size = self.size


class TaskRow(ButtonBehavior, Card):
    """A daily task.  Tapping anywhere on the row completes / uncompletes it."""

    task = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        kwargs.setdefault("orientation", "horizontal")
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(76))
        kwargs.setdefault("padding", [dp(13), dp(10), dp(12), dp(10)])
        kwargs.setdefault("spacing", dp(10))
        kwargs.setdefault("radius", dp(19))
        super().__init__(**kwargs)
        self._bubble = Bubble()
        self.add_widget(self._bubble)
        text_box = BoxLayout(orientation="vertical", spacing=dp(2))
        self._title = Label(
            text="",
            font_name=theme.FONT_CN_BOLD,
            font_size=sp(15.5),
            color=theme.INK,
            halign="left",
            valign="middle",
            shorten=True,
            shorten_from="right",
        )
        self._title.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        self._meta = Label(
            text="",
            font_name=theme.FONT_CN,
            font_size=theme.FS_TINY,
            color=theme.MUTED,
            halign="left",
            valign="middle",
            shorten=True,
            shorten_from="right",
        )
        self._meta.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        text_box.add_widget(self._title)
        text_box.add_widget(self._meta)
        self.add_widget(text_box)
        self._points = Pill(text="★ 2", bg_color=theme.HONEY_SOFT, color=theme.HONEY_DARK)
        self.add_widget(self._points)
        self._check = CheckMark()
        self.add_widget(self._check)
        self.bind(task=self._apply, state=self._on_state)
        self._apply()

    def _apply(self, *_):
        task = self.task or {}
        done = bool(task.get("done"))
        color = task.get("color", "#FF7A66")
        from kivy.utils import get_color_from_hex

        accent = get_color_from_hex(color) if isinstance(color, str) else color
        self.radius = dp(19)
        self._bubble.text = str(task.get("icon") or "星")[:1]
        self._bubble.bubble_color = accent
        self._bubble.opacity = 0.45 if done else 1
        self._title.text = task.get("title", "")
        self._title.color = theme.MUTED if done else theme.INK
        schedule = theme.SCHEDULE_LABELS.get(task.get("schedule", "daily"), "每天")
        self._meta.text = ("已完成 · " if done else f"{schedule} · ") + f"{task.get('points', 0)} 颗星"
        self._meta.color = theme.CORAL_DARK if done else theme.MUTED
        self._points.text = ("＋" if done else "★ ") + str(task.get("points", 0))
        self._points.color = theme.HONEY_DARK if not done else theme.MINT_DARK
        self._points.bg_color = theme.HONEY_SOFT if not done else theme.MINT_SOFT
        self._check.accent = accent
        self._check.done = done
        self.bg_color = theme.CORAL_WASH if done else theme.CARD

    def _on_state(self, *_):
        self.opacity = 0.82 if self.state == "down" else 1.0

    def on_release(self):
        if not self.task:
            return
        from kivy.app import App

        app = App.get_running_app()
        if app:
            app.toggle_task(self.task["id"])


class ManageTaskRow(ButtonBehavior, Card):
    task = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        kwargs.setdefault("orientation", "horizontal")
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(70))
        kwargs.setdefault("padding", [dp(13), dp(9), dp(14), dp(9)])
        kwargs.setdefault("spacing", dp(10))
        kwargs.setdefault("radius", dp(19))
        super().__init__(**kwargs)
        self._bubble = Bubble(size=(dp(42), dp(42)))
        self.add_widget(self._bubble)
        text_box = BoxLayout(orientation="vertical", spacing=dp(2))
        self._title = Label(
            text="",
            font_name=theme.FONT_CN_BOLD,
            font_size=sp(15.5),
            color=theme.INK,
            halign="left",
            valign="middle",
            shorten=True,
            shorten_from="right",
        )
        self._title.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        self._meta = Label(
            text="",
            font_name=theme.FONT_CN,
            font_size=theme.FS_TINY,
            color=theme.MUTED,
            halign="left",
            valign="middle",
        )
        self._meta.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        text_box.add_widget(self._title)
        text_box.add_widget(self._meta)
        self.add_widget(text_box)
        self._points = Pill(text="★ 2", bg_color=theme.HONEY_SOFT, color=theme.HONEY_DARK)
        self.add_widget(self._points)
        arrow = Label(
            text="›",
            font_name=theme.FONT_CN,
            font_size=sp(24),
            color=theme.MUTED,
            size_hint=(None, None),
            size=(dp(14), dp(28)),
        )
        self.add_widget(arrow)
        self.bind(task=self._apply, state=self._on_state)
        self._apply()

    def _apply(self, *_):
        task = self.task or {}
        from kivy.utils import get_color_from_hex

        color = task.get("color", "#FF7A66")
        self._bubble.bubble_color = (
            get_color_from_hex(color) if isinstance(color, str) else color
        )
        self._bubble.text = str(task.get("icon") or "星")[:1]
        self._title.text = task.get("title", "")
        schedule = theme.SCHEDULE_LABELS.get(task.get("schedule", "daily"), "每天")
        self._meta.text = f"{schedule} · 完成后获得 {task.get('points', 0)} 颗星"
        self._points.text = f"★ {task.get('points', 0)}"

    def _on_state(self, *_):
        self.opacity = 0.82 if self.state == "down" else 1.0

    def on_release(self):
        if not self.task:
            return
        from kivy.app import App

        app = App.get_running_app()
        if app:
            app.open_task_editor(self.task)


class PhotoMini(ButtonBehavior, Card):
    photo = ObjectProperty(None, allownone=True)
    thumb_path = StringProperty("")
    date_text = StringProperty("")

    def __init__(self, **kwargs):
        kwargs.setdefault("orientation", "vertical")
        kwargs.setdefault("padding", dp(6))
        kwargs.setdefault("spacing", dp(4))
        kwargs.setdefault("radius", dp(16))
        kwargs.setdefault("bg_color", theme.CARD)
        super().__init__(**kwargs)
        self._image = _PhotoImage()
        self.add_widget(self._image)
        self._date = Label(
            text=self.date_text,
            font_name=theme.FONT_CN,
            font_size=theme.FS_TINY,
            color=theme.MUTED,
            size_hint_y=None,
            height=dp(18),
            halign="center",
        )
        self._date.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        self.add_widget(self._date)
        self.bind(thumb_path=self._apply_image, date_text=self._apply_date)
        self._apply_image()
        self._apply_date()

    def _apply_image(self, *_):
        self._image.source = self.thumb_path

    def _apply_date(self, *_):
        self._date.text = self.date_text





class PhotoAddTile(ButtonBehavior, Card):
    def __init__(self, **kwargs):
        kwargs.setdefault("bg_color", theme.CORAL_WASH)
        kwargs.setdefault("shadow", False)
        kwargs.setdefault("radius", dp(18))
        super().__init__(**kwargs)
        with self.canvas.before:
            self._dash_color = Color(*rgba(theme.CORAL, 0.32))
            self._dash = Line(width=dp(1.2), dash_offset=dp(4))
        self.bind(pos=self._sync, size=self._sync)
        self._sync()
        box = BoxLayout(orientation="vertical", spacing=dp(4))
        star = Label(
            text="＋",
            font_name=theme.FONT_CN,
            font_size=sp(28),
            color=theme.CORAL,
            size_hint_y=None,
            height=dp(36),
        )
        text = Label(
            text="放进一张照片",
            font_name=theme.FONT_CN,
            font_size=theme.FS_TINY,
            color=theme.CORAL_DARK,
            size_hint_y=None,
            height=dp(20),
        )
        box.add_widget(Widget())
        box.add_widget(star)
        box.add_widget(text)
        box.add_widget(Widget())
        self.add_widget(box)

    def _sync(self, *_):
        r = dp(18)
        self._dash.rounded_rectangle = (
            self.x + dp(2),
            self.y + dp(2),
            max(0, self.width - dp(4)),
            max(0, self.height - dp(4)),
            r,
        )
