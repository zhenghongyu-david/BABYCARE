from __future__ import annotations

from kivy.graphics import Color, Ellipse
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from .. import theme
from ..ui.widgets import (
    Card,
    InitialAvatar,
    PhotoAddTile,
    PhotoMini,
    Pill,
    PrimaryButton,
    ProgressRing,
    SectionTitle,
    TaskRow,
    WrappedLabel,
)
from .base import PageScreen


class HeroCard(Card):
    """The coral summary card: points on the left, today's ring on the right."""

    def __init__(self, state, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint_y=None,
            height=dp(214),
            padding=[dp(20), dp(17), dp(20), dp(16)],
            spacing=dp(5),
            radius=dp(26),
            bg_color=theme.CORAL,
            **kwargs,
        )
        with self.canvas.before:
            self._glow_color = Color(1, 1, 1, 0.075)
            self._glow = Ellipse()
            self._glow2_color = Color(1, 1, 1, 0.055)
            self._glow2 = Ellipse()
            self._dot_color = Color(1, 1, 1, 0.45)
            self._dot1 = Ellipse()
            self._dot2 = Ellipse()
        self.bind(pos=self._decorate, size=self._decorate)
        self._decorate()

        top = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(26),
            spacing=dp(6),
        )
        eyebrow = Label(
            text="我的星星口袋",
            font_name=theme.FONT_CN,
            font_size=theme.FS_SMALL,
            color=(1, 1, 1, 0.78),
            halign="left",
            valign="middle",
            size_hint_x=1,
        )
        eyebrow.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        top.add_widget(eyebrow)
        top.add_widget(
            Pill(
                text=f"今天 +{state.today_points}",
                bg_color=(1, 1, 1, 0.18),
                color=theme.WHITE,
                font_size=theme.FS_TINY,
            )
        )
        self.add_widget(top)

        middle = BoxLayout(
            orientation="horizontal",
            size_hint_y=1,
            spacing=dp(4),
        )
        left = BoxLayout(orientation="vertical", spacing=dp(0))
        value = Label(
            text=f"[size={int(sp(46))}][b]{state.total_points}[/b][/size] [size={int(sp(13))}]颗[/size]",
            font_name=theme.FONT_CN_BOLD,
            font_size=sp(46),
            markup=True,
            color=theme.WHITE,
            halign="left",
            valign="bottom",
            size_hint_y=None,
            height=dp(62),
        )
        value.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        left.add_widget(value)
        sub = Label(
            text="一点一点，攒成闪闪发光的童年",
            font_name=theme.FONT_CN,
            font_size=theme.FS_TINY,
            color=(1, 1, 1, 0.72),
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(20),
        )
        sub.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        left.add_widget(sub)
        middle.add_widget(left)

        ring_box = FloatLayout(size_hint=(None, None), size=(dp(100), dp(100)))
        ring = ProgressRing(
            size=(dp(100), dp(100)),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            progress=state.progress,
            track_color=(1, 1, 1, 0.22),
            bar_color=theme.WHITE,
            line_width=dp(8),
        )
        ring_box.add_widget(ring)
        ring_text = Label(
            text=f"{state.today_done}/{state.today_total}",
            font_name=theme.FONT_CN_BOLD,
            font_size=sp(20),
            color=theme.WHITE,
            halign="center",
            valign="middle",
            pos_hint={"center_x": 0.5, "center_y": 0.56},
            size_hint=(None, None),
            size=(dp(80), dp(26)),
        )
        ring_box.add_widget(ring_text)
        ring_caption = Label(
            text="今日完成",
            font_name=theme.FONT_CN,
            font_size=sp(9.5),
            color=(1, 1, 1, 0.7),
            halign="center",
            valign="middle",
            pos_hint={"center_x": 0.5, "center_y": 0.36},
            size_hint=(None, None),
            size=(dp(80), dp(18)),
        )
        ring_box.add_widget(ring_caption)
        middle.add_widget(ring_box)
        self.add_widget(middle)

        message = Label(
            text=state.today_message,
            font_name=theme.FONT_CN,
            font_size=theme.FS_TINY,
            color=(1, 1, 1, 0.86),
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(20),
            shorten=True,
            shorten_from="right",
        )
        message.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        self.add_widget(message)

    def _decorate(self, *_):
        x, y = self.pos
        w, h = self.size
        self._glow.pos = (x + w - dp(96), y + h - dp(98))
        self._glow.size = (dp(168), dp(168))
        self._glow2.pos = (x - dp(42), y - dp(58))
        self._glow2.size = (dp(126), dp(126))
        self._dot1.pos = (x + w - dp(30), y + dp(28))
        self._dot1.size = (dp(5), dp(5))
        self._dot2.pos = (x + w - dp(44), y + dp(40))
        self._dot2.size = (dp(3), dp(3))


class TodayScreen(PageScreen):
    def rebuild(self):
        self.content.clear_widgets()
        self.add(self.brand_bar())
        self.add(self._greeting())
        self.add(HeroCard(self.state))
        self.add(self._tasks_heading())
        self._build_tasks()
        self.add(self._photos_heading())
        self._build_photo_strip()
        note = Label(
            text="每一颗星，都是成长的小证据。",
            font_name=theme.FONT_CN,
            font_size=theme.FS_TINY,
            color=theme.MUTED,
            size_hint_y=None,
            height=dp(26),
            halign="center",
            valign="middle",
        )
        note.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        self.add(note)

    def _greeting(self):
        row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(76),
            spacing=dp(10),
            padding=[0, dp(2), 0, 0],
        )
        text_box = BoxLayout(orientation="vertical", spacing=dp(3))
        greeting = Label(
            text=f"{self.state.greeting}，{self.state.name}",
            font_name=theme.FONT_CN_BOLD,
            font_size=sp(25),
            color=theme.INK,
            halign="left",
            valign="bottom",
            size_hint_y=None,
            height=dp(34),
            shorten=True,
            shorten_from="right",
        )
        greeting.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        text_box.add_widget(greeting)
        sub = Label(
            text=f"{self.state.date_text}  ·  {self.state.age_text}",
            font_name=theme.FONT_CN,
            font_size=theme.FS_SMALL,
            color=theme.MUTED,
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(22),
            shorten=True,
        )
        sub.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        text_box.add_widget(sub)
        row.add_widget(text_box)
        row.add_widget(
            InitialAvatar(
                name=self.state.name,
                diameter=dp(54),
                size_hint=(None, None),
                size=(dp(54), dp(54)),
            )
        )
        return row

    def _tasks_heading(self):
        return SectionTitle(
            f"今日任务  {self.state.today_done}/{self.state.today_total}" if self.state.today_total else "今日任务",
            action="管理 ›",
            on_action=lambda: self.app.switch_to("tasks"),
        )

    def _build_tasks(self):
        if not self.state.today_tasks:
            self.add(self._empty_tasks())
            return
        for task in self.state.today_tasks:
            self.add(TaskRow(task=task))

    def _empty_tasks(self):
        card = Card(
            orientation="vertical",
            size_hint_y=None,
            height=dp(166),
            padding=[dp(18), dp(16), dp(18), dp(14)],
            spacing=dp(4),
            radius=dp(20),
            bg_color=theme.CARD_SOFT,
        )
        star = Label(
            text="★",
            font_name=theme.FONT_CN,
            font_size=sp(26),
            color=theme.HONEY,
            size_hint_y=None,
            height=dp(34),
            halign="center",
        )
        star.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        card.add_widget(star)
        title = Label(
            text="今天还没有任务",
            font_name=theme.FONT_CN_BOLD,
            font_size=theme.FS_BODY,
            color=theme.INK,
            size_hint_y=None,
            height=dp(24),
            halign="center",
        )
        title.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        card.add_widget(title)
        body = Label(
            text="先设一个小目标，完成后就能收获星星",
            font_name=theme.FONT_CN,
            font_size=theme.FS_SMALL,
            color=theme.MUTED,
            size_hint_y=None,
            height=dp(22),
            halign="center",
        )
        body.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        card.add_widget(body)
        row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(44), spacing=dp(8))
        row.add_widget(Widget())
        button = PrimaryButton(
            text="添加第一个任务",
            size_hint=(None, None),
            width=dp(174),
            height=dp(42),
            font_size=theme.FS_SMALL,
        )
        button.bind(on_release=lambda *_: self.app.open_task_editor())
        row.add_widget(button)
        row.add_widget(Widget())
        card.add_widget(row)
        return card

    def _photos_heading(self):
        return SectionTitle(
            "今日瞬间",
            action="相册 ›",
            on_action=lambda: self.app.switch_to("album"),
        )

    def _build_photo_strip(self):
        wrapper = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(146),
        )
        strip = BoxLayout(
            orientation="horizontal",
            size_hint=(None, 1),
            height=dp(146),
            spacing=dp(10),
        )
        strip.bind(minimum_width=strip.setter("width"))
        for photo in self.state.photos[:6]:
            mini = PhotoMini(
                size_hint=(None, None),
                size=(dp(112), dp(142)),
                thumb_path=self.state.repo.photo_path(photo, thumb=True),
                date_text=self._short_date(photo.get("taken_on", "")),
            )
            mini.bind(on_release=lambda inst, photo=photo: self.app.open_photo(photo))
            strip.add_widget(mini)
        add = PhotoAddTile(size_hint=(None, None), size=(dp(112), dp(142)))
        add.bind(on_release=lambda *_: self.app.pick_photo())
        strip.add_widget(add)
        if not self.state.photos:
            info = Card(
                orientation="vertical",
                size_hint=(None, None),
                size=(dp(190), dp(142)),
                padding=[dp(16), dp(14)],
                spacing=dp(4),
                radius=dp(18),
                bg_color=theme.CARD_SOFT,
                shadow=False,
            )
            info.add_widget(Widget())
            line1 = Label(
                text="把今天的小进步",
                font_name=theme.FONT_CN_BOLD,
                font_size=theme.FS_SMALL,
                color=theme.INK,
                size_hint_y=None,
                height=dp(22),
                halign="left",
            )
            line1.bind(size=lambda inst, val: setattr(inst, "text_size", val))
            info.add_widget(line1)
            line2 = WrappedLabel(
                text="拍下来，收进成长相册里。",
                font_size=theme.FS_TINY,
                color=theme.MUTED,
                size_hint_y=None,
            )
            info.add_widget(line2)
            info.add_widget(Widget())
            strip.add_widget(info)
        scroll = ScrollView(
            do_scroll_x=True,
            do_scroll_y=False,
            bar_width=0,
            scroll_type=["content"],
        )
        scroll.add_widget(strip)
        wrapper.add_widget(scroll)
        self.add(wrapper)

    @staticmethod
    def _short_date(iso: str) -> str:
        try:
            _, month, day = iso.split("-")
            return f"{int(month)}月{int(day)}日"
        except ValueError:
            return iso
