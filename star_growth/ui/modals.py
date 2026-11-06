"""Bottom-sheet style dialogs used by the diary."""
from __future__ import annotations

from datetime import date
from typing import Any, Callable

from kivy.app import App
from kivy.graphics import Color, Ellipse, Line, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex

from .. import theme
from ..repository import RepositoryError
from .widgets import Card, Pill, PrimaryButton, TinyButton, WrappedLabel, rgba


class BaseModal(ModalView):
    def __init__(self, **kwargs):
        kwargs.setdefault("size_hint", (1, 1))
        kwargs.setdefault("auto_dismiss", False)
        kwargs.setdefault("background_color", (0, 0, 0, 0))
        kwargs.setdefault("background", "atlas://data/images/defaulttheme/button")
        super().__init__(**kwargs)
        self.app = App.get_running_app()
        if self.app and hasattr(self.app, "register_modal"):
            self.app.register_modal(self)
        self.bind(on_dismiss=self._forget)
        self.stage = FloatLayout()
        with self.stage.canvas.before:
            self._dim_color = Color(0.10, 0.08, 0.12, 0.52)
            self._dim = RoundedRectangle(radius=[0])
        self.stage.bind(pos=self._sync_dim, size=self._sync_dim)
        self.add_widget(self.stage)

    def _sync_dim(self, *_):
        self._dim.pos = self.stage.pos
        self._dim.size = self.stage.size

    def _forget(self, *_):
        if self.app and hasattr(self.app, "forget_modal"):
            self.app.forget_modal(self)

    def close(self):
        self.dismiss()


class Sheet(BaseModal):
    """A white, rounded sheet with a title row and a scrolling body."""

    title = StringProperty("")
    height_ratio = NumericProperty(0.86)

    def __init__(self, title: str, **kwargs):
        self._title_text = title
        super().__init__(**kwargs)
        self.card = Card(
            orientation="vertical",
            padding=[dp(20), dp(16), dp(20), dp(18)],
            spacing=dp(10),
            radius=dp(26),
            bg_color=theme.CARD,
            size_hint=(0.92, self.height_ratio),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )
        self.stage.add_widget(self.card)
        self._header = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(42),
            spacing=dp(8),
        )
        heading = Label(
            text=title,
            font_name=theme.FONT_CN_BOLD,
            font_size=sp(20),
            color=theme.INK,
            halign="left",
            valign="middle",
        )
        heading.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        self._header.add_widget(heading)
        close = TinyButton(
            text="×",
            font_name=theme.FONT_CN,
            font_size=sp(22),
            bg_color=(1, 1, 1, 0),
            text_color=theme.MUTED,
            size_hint=(None, None),
            size=(dp(36), dp(36)),
        )
        close.bind(on_release=lambda *_: self.dismiss())
        self._header.add_widget(close)
        self.card.add_widget(self._header)
        self.body = BoxLayout(
            orientation="vertical",
            spacing=dp(12),
            size_hint_y=None,
            padding=[0, 0, 0, dp(8)],
        )
        self.body.bind(minimum_height=self.body.setter("height"))
        self.scroll = ScrollView(
            size_hint_y=1,
            bar_width=dp(2),
            bar_color=theme.CORAL_SOFT,
            bar_inactive_color=theme.CORAL_SOFT,
            scroll_type=["bars", "content"],
            effect_cls="ScrollEffect",
        )
        self.scroll.add_widget(self.body)
        self.card.add_widget(self.scroll)
        self.footer = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(54),
            spacing=dp(10),
        )
        self.card.add_widget(self.footer)


class Field(BoxLayout):
    def __init__(
        self,
        label: str,
        hint: str = "",
        text: str = "",
        multiline: bool = False,
        height: float = dp(52),
        **kwargs,
    ):
        kwargs.setdefault("orientation", "vertical")
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", height + dp(24))
        kwargs.setdefault("spacing", dp(5))
        super().__init__(**kwargs)
        hint_label = Label(
            text=label,
            font_name=theme.FONT_CN,
            font_size=theme.FS_TINY,
            color=theme.MUTED,
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(20),
        )
        hint_label.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        self.add_widget(hint_label)
        shell = Card(
            orientation="vertical",
            size_hint_y=None,
            height=height,
            padding=[dp(4), dp(2), dp(4), dp(2)],
            radius=dp(13),
            bg_color=theme.BG,
            shadow=False,
            border=True,
        )
        self.input = TextInput(
            text=text,
            hint_text=hint,
            font_name=theme.FONT_CN,
            font_size=theme.FS_BODY,
            multiline=multiline,
            background_normal="",
            background_active="",
            background_disabled_normal="",
            background_color=(0, 0, 0, 0),
            foreground_color=theme.INK,
            hint_text_color=theme.MUTED,
            cursor_color=theme.CORAL,
            cursor_width=dp(1.6),
            padding=[dp(11), dp(10), dp(11), dp(10)],
            write_tab=False,
        )
        shell.add_widget(self.input)
        self.add_widget(shell)


class Segmented(BoxLayout):
    value = StringProperty("")

    def __init__(self, options: list[tuple[str, str]], value: str, on_change: Callable, **kwargs):
        kwargs.setdefault("orientation", "horizontal")
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(40))
        kwargs.setdefault("spacing", dp(6))
        super().__init__(**kwargs)
        self.options = options
        self.value = value
        self.on_change = on_change
        self._buttons: dict[str, TinyButton] = {}
        for key, label in options:
            button = TinyButton(
                text=label,
                bg_color=theme.BG_DEEP,
                text_color=theme.MUTED,
                size_hint=(1, None),
                height=dp(38),
                font_size=theme.FS_SMALL,
                radius=dp(11),
            )
            button.bind(on_release=lambda inst, key=key: self.select(key))
            self._buttons[key] = button
            self.add_widget(button)
        self._paint()

    def select(self, key: str):
        self.value = key
        self._paint()
        self.on_change(key)

    def _paint(self):
        for key, button in self._buttons.items():
            active = key == self.value
            button._base_bg = rgba(theme.CORAL if active else theme.BG_DEEP)
            button._color.rgba = button._base_bg
            button.color = theme.WHITE if active else theme.MUTED
            button.font_name = theme.FONT_CN_BOLD if active else theme.FONT_CN


class ColorChoice(ButtonBehavior, Widget):
    color_hex = StringProperty("#FF7A66")
    selected = BooleanProperty(False)

    def __init__(self, **kwargs):
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("size", (dp(36), dp(36)))
        super().__init__(**kwargs)
        self.bind(pos=self._redraw, size=self._redraw, selected=self._redraw, color_hex=self._redraw)
        self._redraw()

    def _redraw(self, *_):
        self.canvas.clear()
        cx, cy = self.center
        color = get_color_from_hex(self.color_hex)
        with self.canvas:
            if self.selected:
                Color(*theme.INK)
                Line(circle=(cx, cy, dp(15)), width=dp(1.7))
            Color(*color)
            Ellipse(pos=(cx - dp(10), cy - dp(10)), size=(dp(20), dp(20)))


class IconChoice(ButtonBehavior, FloatLayout):
    icon = StringProperty("星")
    selected = BooleanProperty(False)
    bubble_color = ListProperty(theme.CORAL)

    def __init__(self, **kwargs):
        kwargs.setdefault("size_hint", (1, 1))
        kwargs.setdefault("size", (dp(44), dp(44)))
        super().__init__(**kwargs)
        self._bubble = Label(
            text=self.icon,
            font_name=theme.FONT_CN_BOLD,
            font_size=sp(18),
            color=theme.WHITE,
            halign="center",
            valign="middle",
        )
        self.add_widget(self._bubble)
        with self.canvas.before:
            self._fill_color = Color(*rgba(self.bubble_color))
            self._fill = Ellipse()
        with self.canvas.after:
            self._ring_color = Color(*theme.INK)
            self._ring = Line(width=dp(1.6))
        self.bind(
            pos=self._redraw,
            size=self._redraw,
            icon=self._redraw,
            selected=self._redraw,
            bubble_color=self._redraw,
        )
        self._redraw()

    def _redraw(self, *_):
        self._bubble.text = self.icon
        self._bubble.pos = self.pos
        self._bubble.size = self.size
        diameter = max(dp(30), min(self.width, self.height) - dp(4))
        self._fill.pos = (
            self.center_x - diameter / 2,
            self.center_y - diameter / 2,
        )
        self._fill.size = (diameter, diameter)
        self._fill_color.rgba = rgba(self.bubble_color)
        self._ring.circle = (
            self.center_x,
            self.center_y,
            diameter / 2 + dp(2),
        )
        self._ring_color.a = 1 if self.selected else 0


class TaskEditor(Sheet):
    def __init__(
        self,
        task: dict[str, Any] | None,
        on_save: Callable[[dict[str, Any]], bool],
        on_delete: Callable[[int], None] | None = None,
        **kwargs,
    ):
        self.task = task
        self._on_save = on_save
        self._on_delete = on_delete
        self._points = int(task.get("points", 2)) if task else 2
        self._icon = task.get("icon", "读") if task else "读"
        self._color = task.get("color", "#FF7A66") if task else "#FF7A66"
        self._schedule = task.get("schedule", "daily") if task else "daily"
        super().__init__("编辑任务" if task else "新建一个小任务", height_ratio=0.68, **kwargs)

        name_field = Field("任务名称", "比如：自己穿鞋、读一本绘本", task.get("title", "") if task else "")
        self.body.add_widget(name_field)
        self._name = name_field.input

        points_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(48),
            spacing=dp(10),
        )
        label = Label(
            text="完成奖励",
            font_name=theme.FONT_CN,
            font_size=theme.FS_SMALL,
            color=theme.MUTED,
            halign="left",
            valign="middle",
        )
        label.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        points_row.add_widget(label)
        minus = TinyButton(
            text="－",
            font_size=sp(20),
            bg_color=theme.BG_DEEP,
            text_color=theme.INK,
            size_hint=(None, None),
            size=(dp(36), dp(36)),
        )
        minus.bind(on_release=lambda *_: self._step_points(-1))
        points_row.add_widget(minus)
        self._points_label = Label(
            text=self._points_text(),
            font_name=theme.FONT_CN_BOLD,
            font_size=theme.FS_BODY,
            color=theme.HONEY_DARK,
            size_hint=(None, None),
            size=(dp(58), dp(38)),
            halign="center",
            valign="middle",
        )
        self._points_label.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        points_row.add_widget(self._points_label)
        plus = TinyButton(
            text="＋",
            font_size=sp(20),
            bg_color=theme.CORAL_SOFT,
            text_color=theme.CORAL_DARK,
            size_hint=(None, None),
            size=(dp(36), dp(36)),
        )
        plus.bind(on_release=lambda *_: self._step_points(1))
        points_row.add_widget(plus)
        self.body.add_widget(points_row)

        schedule_label = Label(
            text="什么时候做",
            font_name=theme.FONT_CN,
            font_size=theme.FS_TINY,
            color=theme.MUTED,
            size_hint_y=None,
            height=dp(20),
            halign="left",
            valign="middle",
        )
        schedule_label.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        self.body.add_widget(schedule_label)
        self._segmented = Segmented(
            [("daily", "每天"), ("weekdays", "周一到周五"), ("weekend", "周末")],
            self._schedule,
            self._set_schedule,
        )
        self.body.add_widget(self._segmented)

        icon_label = Label(
            text="选一个小图标",
            font_name=theme.FONT_CN,
            font_size=theme.FS_TINY,
            color=theme.MUTED,
            size_hint_y=None,
            height=dp(20),
            halign="left",
            valign="middle",
        )
        icon_label.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        self.body.add_widget(icon_label)
        icon_row = GridLayout(
            cols=5,
            size_hint_y=None,
            height=dp(98),
            spacing=dp(7),
            row_default_height=dp(44),
            row_force_default=True,
        )
        self._icon_choices: list[IconChoice] = []
        for icon in theme.TASK_ICONS:
            choice = IconChoice(
                icon=icon,
                bubble_color=theme.LAVENDER,
                size_hint=(1, 1),
            )
            if icon == self._icon:
                choice.selected = True
            choice.bind(on_release=lambda inst, icon=icon: self._set_icon(icon))
            self._icon_choices.append(choice)
            icon_row.add_widget(choice)
        self.body.add_widget(icon_row)

        color_label = Label(
            text="换一种颜色",
            font_name=theme.FONT_CN,
            font_size=theme.FS_TINY,
            color=theme.MUTED,
            size_hint_y=None,
            height=dp(20),
            halign="left",
            valign="middle",
        )
        color_label.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        self.body.add_widget(color_label)
        color_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(40),
            spacing=dp(6),
        )
        self._color_choices: list[ColorChoice] = []
        for _, hex_value, _ in theme.TASK_COLORS:
            choice = ColorChoice(color_hex=hex_value)
            if hex_value.lower() == self._color.lower():
                choice.selected = True
            choice.bind(on_release=lambda inst, hex_value=hex_value: self._set_color(hex_value))
            self._color_choices.append(choice)
            color_row.add_widget(choice)
        self.body.add_widget(color_row)

        self._preview = Card(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(62),
            padding=[dp(10), dp(8)],
            spacing=dp(8),
            radius=dp(15),
            bg_color=theme.BG,
            shadow=False,
        )
        self._preview_bubble = IconChoice(
            icon=self._icon,
            bubble_color=theme.CORAL,
            size_hint=(None, None),
            size=(dp(44), dp(44)),
        )
        self._preview_bubble.opacity = 1
        self._preview.add_widget(self._preview_bubble)
        self._preview_text = Label(
            text=task.get("title", "任务名称") if task else "任务名称",
            font_name=theme.FONT_CN_BOLD,
            font_size=theme.FS_BODY,
            color=theme.INK,
            halign="left",
            valign="middle",
            shorten=True,
            shorten_from="right",
        )
        self._preview_text.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        self._preview.add_widget(self._preview_text)
        self._preview_points = Pill(text="★ 2", bg_color=theme.HONEY_SOFT, color=theme.HONEY_DARK)
        self._preview.add_widget(self._preview_points)
        self.body.add_widget(self._preview)

        hint = Card(
            orientation="vertical",
            size_hint_y=None,
            height=dp(66),
            padding=[dp(14), dp(10)],
            spacing=dp(2),
            radius=dp(14),
            bg_color=theme.CORAL_WASH,
            shadow=False,
        )
        hint_title = Label(
            text="每天都会重新开始",
            font_name=theme.FONT_CN_BOLD,
            font_size=theme.FS_TINY,
            color=theme.CORAL_DARK,
            size_hint_y=None,
            height=dp(18),
            halign="left",
        )
        hint_title.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        hint.add_widget(hint_title)
        hint_body = WrappedLabel(
            text="完成状态会在零点刷新；之前获得的星星会留在记录里。",
            font_size=theme.FS_TINY,
            color=theme.MUTED,
            size_hint_y=None,
        )
        hint.add_widget(hint_body)
        self.body.add_widget(hint)

        self._error = Label(
            text="",
            font_name=theme.FONT_CN,
            font_size=theme.FS_SMALL,
            color=theme.CORAL_DARK,
            size_hint_y=None,
            height=dp(20),
            halign="left",
            valign="middle",
        )
        self._error.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        self.body.add_widget(self._error)

        if task and on_delete:
            delete = TinyButton(
                text="删除任务",
                bg_color=theme.CORAL_SOFT,
                text_color=theme.CORAL_DARK,
                height=dp(48),
                font_size=theme.FS_SMALL,
            )
            delete.bind(on_release=lambda *_: self._confirm_delete())
            self.footer.add_widget(delete)
        self.footer.add_widget(Widget())
        save = PrimaryButton(text="保存任务", size_hint=(None, None), width=dp(150))
        save.bind(on_release=lambda *_: self._save())
        self.footer.add_widget(save)
        self._name.bind(text=self._update_preview)
        self._update_preview()

    def _points_text(self):
        return f"★ {self._points}"

    def _step_points(self, delta: int):
        self._points = max(1, min(10, self._points + delta))
        self._points_label.text = self._points_text()
        self._update_preview()

    def _set_schedule(self, value: str):
        self._schedule = value

    def _set_icon(self, icon: str):
        self._icon = icon
        for choice in self._icon_choices:
            choice.selected = choice.icon == icon
        self._preview_bubble.icon = icon
        self._update_preview()

    def _set_color(self, value: str):
        self._color = value
        for choice in self._color_choices:
            choice.selected = choice.color_hex.lower() == value.lower()
        self._preview_bubble.bubble_color = get_color_from_hex(value)
        self._update_preview()

    def _update_preview(self, *_):
        title = (self._name.text or "").strip() or "任务名称"
        if len(title) > 13:
            title = title[:13] + "…"
        self._preview_text.text = title
        self._preview_points.text = self._points_text()
        self._preview_bubble.bubble_color = get_color_from_hex(self._color)
        self._preview_bubble.icon = self._icon

    def _save(self):
        payload = {
            "title": (self._name.text or "").strip(),
            "points": self._points,
            "icon": self._icon,
            "color": self._color,
            "schedule": self._schedule,
        }
        try:
            ok = self._on_save(payload)
        except RepositoryError as exc:
            self._error.text = str(exc)
            return
        if ok is not False:
            self.dismiss()

    def _confirm_delete(self):
        ConfirmDialog(
            title="删除这个任务？",
            message="今天已经获得的星星也会一起收回，之前的记录会保留。",
            confirm_text="删除",
            on_confirm=lambda: self._do_delete(),
        ).open()

    def _do_delete(self):
        self.dismiss()
        if self._on_delete and self.task:
            self._on_delete(int(self.task["id"]))


class PhotoEditor(Sheet):
    def __init__(
        self,
        source_path: str,
        on_save: Callable[[str, str, str], bool],
        **kwargs,
    ):
        self._source = source_path
        self._on_save = on_save
        super().__init__("收藏这一刻", height_ratio=0.62, **kwargs)

        preview_shell = Card(
            orientation="vertical",
            size_hint_y=None,
            height=dp(220),
            padding=dp(6),
            radius=dp(18),
            bg_color=theme.BG,
            shadow=False,
        )
        preview = Image(
            source=source_path,
            fit_mode="contain",
            mipmap=True,
        )
        preview_shell.add_widget(preview)
        self.body.add_widget(preview_shell)

        self._caption = Field("写一句话（可选）", "今天第一次自己穿鞋", "")
        self._caption.input.multiline = False
        self.body.add_widget(self._caption)

        self._date = Field("日期", "YYYY-MM-DD", date.today().isoformat())
        self.body.add_widget(self._date)

        note = Label(
            text="照片会复制到 App 的本地相册，不会上传到任何服务器。",
            font_name=theme.FONT_CN,
            font_size=theme.FS_TINY,
            color=theme.MUTED,
            size_hint_y=None,
            height=dp(34),
            halign="left",
            valign="middle",
        )
        note.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], dp(34))))
        self.body.add_widget(note)

        self._error = Label(
            text="",
            font_name=theme.FONT_CN,
            font_size=theme.FS_SMALL,
            color=theme.CORAL_DARK,
            size_hint_y=None,
            height=dp(20),
        )
        self.body.add_widget(self._error)

        cancel = TinyButton(
            text="取消",
            bg_color=theme.BG_DEEP,
            text_color=theme.MUTED,
            height=dp(48),
            font_size=theme.FS_SMALL,
        )
        cancel.bind(on_release=lambda *_: self.dismiss())
        self.footer.add_widget(cancel)
        self.footer.add_widget(Widget())
        save = PrimaryButton(text="保存到相册", size_hint=(None, None), width=dp(160))
        save.bind(on_release=lambda *_: self._save())
        self.footer.add_widget(save)

    def _save(self):
        caption = (self._caption.input.text or "").strip()
        taken_on = (self._date.input.text or "").strip()
        try:
            date.fromisoformat(taken_on)
        except ValueError:
            self._error.text = "日期格式应为 YYYY-MM-DD"
            return
        try:
            ok = self._on_save(self._source, caption, taken_on)
        except Exception as exc:
            self._error.text = str(exc)
            return
        if ok is not False:
            self.dismiss()


class PhotoViewer(Sheet):
    def __init__(
        self,
        photo: dict[str, Any],
        path: str,
        on_delete: Callable[[int], None],
        **kwargs,
    ):
        self.photo = photo
        self._on_delete = on_delete
        super().__init__("成长瞬间", height_ratio=0.60, **kwargs)

        image_shell = Card(
            orientation="vertical",
            size_hint_y=None,
            height=dp(330),
            padding=dp(6),
            radius=dp(20),
            bg_color=theme.BG,
            shadow=False,
        )
        image_shell.add_widget(
            Image(
                source=path,
                fit_mode="contain",
                mipmap=True,
            )
        )
        self.body.add_widget(image_shell)

        self._caption = WrappedLabel(
            text=photo.get("caption") or "这一刻，值得好好收藏。",
            font_size=theme.FS_BODY,
            color=theme.INK,
            size_hint_y=None,
        )
        self.body.add_widget(self._caption)
        taken = photo.get("taken_on", "")
        try:
            parsed = date.fromisoformat(taken)
            nice = f"{parsed.year}年{parsed.month}月{parsed.day}日"
        except ValueError:
            nice = taken
        meta = Label(
            text=f"{nice} · 照片只保存在本机",
            font_name=theme.FONT_CN,
            font_size=theme.FS_TINY,
            color=theme.MUTED,
            size_hint_y=None,
            height=dp(26),
            halign="left",
            valign="middle",
        )
        meta.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        self.body.add_widget(meta)

        delete = TinyButton(
            text="删除这张照片",
            bg_color=theme.CORAL_SOFT,
            text_color=theme.CORAL_DARK,
            height=dp(46),
            font_size=theme.FS_SMALL,
        )
        delete.bind(on_release=lambda *_: self._confirm_delete())
        self.footer.add_widget(delete)
        self.footer.add_widget(Widget())
        close = PrimaryButton(
            text="收好",
            size_hint=(None, None),
            width=dp(130),
            bg_color=theme.CORAL,
        )
        close.bind(on_release=lambda *_: self.dismiss())
        self.footer.add_widget(close)

    def _confirm_delete(self):
        ConfirmDialog(
            title="删除这张照片？",
            message="照片文件也会从这台设备上移除，无法恢复。",
            confirm_text="删除",
            on_confirm=self._do_delete,
        ).open()

    def _do_delete(self):
        self.dismiss()
        self._on_delete(int(self.photo["id"]))


class SettingsSheet(Sheet):
    def __init__(
        self,
        name: str,
        birthday: str | None,
        on_save: Callable[[str, str | None], bool],
        on_reset: Callable[[], None],
        **kwargs,
    ):
        self._on_save = on_save
        self._on_reset = on_reset
        super().__init__("宝贝资料", height_ratio=0.60, **kwargs)

        intro = WrappedLabel(
            text="把这些小信息告诉我，称呼和年龄会更贴近你们。",
            font_size=theme.FS_SMALL,
            color=theme.MUTED,
            size_hint_y=None,
        )
        self.body.add_widget(intro)

        self._name = Field("宝贝的名字", "小宝贝", name or "小宝贝")
        self.body.add_widget(self._name)
        self._birthday = Field(
            "生日（可选）",
            "YYYY-MM-DD",
            birthday or "",
        )
        self.body.add_widget(self._birthday)

        info = Card(
            orientation="vertical",
            size_hint_y=None,
            height=dp(104),
            padding=[dp(14), dp(12)],
            spacing=dp(5),
            radius=dp(16),
            bg_color=theme.MINT_SOFT,
            shadow=False,
        )
        info_title = Label(
            text="数据只在这台设备上",
            font_name=theme.FONT_CN_BOLD,
            font_size=theme.FS_SMALL,
            color=theme.MINT,
            size_hint_y=None,
            height=dp(22),
            halign="left",
        )
        info_title.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        info.add_widget(info_title)
        info_body = WrappedLabel(
            text="任务、积分和照片都保存在本地数据库里，不上传云端，也不需要注册账号。",
            font_size=theme.FS_TINY,
            color=theme.INK_SOFT,
            size_hint_y=None,
        )
        info.add_widget(info_body)
        self.body.add_widget(info)

        self._error = Label(
            text="",
            font_name=theme.FONT_CN,
            font_size=theme.FS_SMALL,
            color=theme.CORAL_DARK,
            size_hint_y=None,
            height=dp(20),
        )
        self.body.add_widget(self._error)

        reset = TinyButton(
            text="清空所有记录",
            bg_color=theme.CORAL_SOFT,
            text_color=theme.CORAL_DARK,
            height=dp(42),
            font_size=theme.FS_SMALL,
        )
        reset.bind(on_release=lambda *_: self._confirm_reset())
        self.body.add_widget(reset)

        self.footer.add_widget(Widget())
        save = PrimaryButton(text="保存资料", size_hint=(None, None), width=dp(150))
        save.bind(on_release=lambda *_: self._save())
        self.footer.add_widget(save)

    def _save(self):
        name = (self._name.input.text or "").strip()
        birthday = (self._birthday.input.text or "").strip() or None
        try:
            ok = self._on_save(name, birthday)
        except RepositoryError as exc:
            self._error.text = str(exc)
            return
        if ok is not False:
            self.dismiss()

    def _confirm_reset(self):
        ConfirmDialog(
            title="清空所有记录？",
            message="任务、积分和照片都会被删除，并恢复成初始状态。这个操作无法撤销。",
            confirm_text="确认清空",
            on_confirm=self._do_reset,
        ).open()

    def _do_reset(self):
        self.dismiss()
        self._on_reset()


class ConfirmDialog(BaseModal):
    def __init__(
        self,
        title: str,
        message: str,
        confirm_text: str,
        on_confirm: Callable,
        **kwargs,
    ):
        self._on_confirm = on_confirm
        super().__init__(**kwargs)
        card = Card(
            orientation="vertical",
            padding=[dp(22), dp(20), dp(22), dp(18)],
            spacing=dp(8),
            radius=dp(24),
            bg_color=theme.CARD,
            size_hint=(0.86, None),
            height=dp(236),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )
        self.stage.add_widget(card)
        heading = Label(
            text=title,
            font_name=theme.FONT_CN_BOLD,
            font_size=sp(19),
            color=theme.INK,
            size_hint_y=None,
            height=dp(32),
            halign="left",
            valign="middle",
        )
        heading.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        card.add_widget(heading)
        body = WrappedLabel(
            text=message,
            font_size=theme.FS_SMALL,
            color=theme.MUTED,
            size_hint_y=None,
        )
        card.add_widget(body)
        card.add_widget(Widget())
        row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(48),
            spacing=dp(10),
        )
        cancel = TinyButton(
            text="再想想",
            bg_color=theme.BG_DEEP,
            text_color=theme.MUTED,
            size_hint=(1, None),
            height=dp(46),
        )
        cancel.bind(on_release=lambda *_: self.dismiss())
        row.add_widget(cancel)
        confirm = PrimaryButton(
            text=confirm_text,
            size_hint=(1, None),
            height=dp(46),
        )
        confirm.bind(on_release=lambda *_: self._confirm())
        row.add_widget(confirm)
        card.add_widget(row)

    def _confirm(self):
        self.dismiss()
        self._on_confirm()
