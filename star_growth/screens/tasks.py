from __future__ import annotations

from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget

from .. import theme
from ..ui.widgets import Card, ManageTaskRow, PrimaryButton, SectionTitle, WrappedLabel
from .base import PageScreen


class TasksScreen(PageScreen):
    def rebuild(self):
        self.content.clear_widgets()
        self.add(self.brand_bar())
        self.add(self.page_title("任务清单", "把想养成的小习惯，变成每天的一颗星"))
        self.add(self._summary())
        self.add(SectionTitle("全部任务"))
        self._build_tasks()
        self.add(self._tip())

    def _summary(self):
        tasks = self.state.tasks
        possible = sum(int(task["points"]) for task in tasks)
        card = Card(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(76),
            padding=[dp(14), dp(10), dp(12), dp(10)],
            spacing=dp(10),
            radius=dp(20),
            bg_color=theme.HONEY_SOFT,
            shadow=False,
        )
        star = Label(
            text="★",
            font_name=theme.FONT_CN,
            font_size=sp(26),
            color=theme.HONEY,
            size_hint=(None, None),
            size=(dp(34), dp(34)),
            halign="center",
            valign="middle",
        )
        card.add_widget(star)
        text_box = BoxLayout(orientation="vertical", spacing=dp(2))
        title = Label(
            text=f"每天最多收获 {possible} 颗星",
            font_name=theme.FONT_CN_BOLD,
            font_size=theme.FS_BODY,
            color=theme.INK,
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(24),
            shorten=True,
        )
        title.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        text_box.add_widget(title)
        sub = Label(
            text=f"共 {len(tasks)} 个每日任务",
            font_name=theme.FONT_CN,
            font_size=theme.FS_TINY,
            color=theme.MUTED,
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(18),
        )
        sub.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        text_box.add_widget(sub)
        card.add_widget(text_box)
        button = PrimaryButton(
            text="＋ 新建",
            size_hint=(None, None),
            width=dp(92),
            height=dp(42),
            font_size=theme.FS_SMALL,
            radius=dp(13),
        )
        button.bind(on_release=lambda *_: self.app.open_task_editor())
        card.add_widget(button)
        return card

    def _build_tasks(self):
        if not self.state.tasks:
            self.add(self._empty())
            return
        for task in self.state.tasks:
            self.add(ManageTaskRow(task=task))

    def _empty(self):
        card = Card(
            orientation="vertical",
            size_hint_y=None,
            height=dp(188),
            padding=[dp(18), dp(18)],
            spacing=dp(6),
            radius=dp(20),
            bg_color=theme.CARD_SOFT,
        )
        star = Label(
            text="★",
            font_name=theme.FONT_CN,
            font_size=sp(30),
            color=theme.HONEY,
            size_hint_y=None,
            height=dp(38),
            halign="center",
        )
        star.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        card.add_widget(star)
        title = Label(
            text="还没有任务",
            font_name=theme.FONT_CN_BOLD,
            font_size=theme.FS_BODY,
            color=theme.INK,
            size_hint_y=None,
            height=dp(24),
            halign="center",
        )
        title.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        card.add_widget(title)
        body = WrappedLabel(
            text="从「自己刷牙」或「读一本绘本」开始，\n把一个好习惯变成每天的小星星。",
            font_size=theme.FS_SMALL,
            color=theme.MUTED,
            halign="center",
            size_hint_y=None,
        )
        card.add_widget(body)
        row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(44), spacing=dp(8))
        row.add_widget(Widget())
        button = PrimaryButton(
            text="添加任务",
            size_hint=(None, None),
            width=dp(140),
            height=dp(42),
            font_size=theme.FS_SMALL,
        )
        button.bind(on_release=lambda *_: self.app.open_task_editor())
        row.add_widget(button)
        row.add_widget(Widget())
        card.add_widget(row)
        return card

    def _tip(self):
        card = Card(
            orientation="vertical",
            size_hint_y=None,
            height=dp(82),
            padding=[dp(16), dp(12)],
            spacing=dp(3),
            radius=dp(16),
            bg_color=theme.CARD_SOFT,
            shadow=False,
        )
        title = Label(
            text="小提示",
            font_name=theme.FONT_CN_BOLD,
            font_size=theme.FS_SMALL,
            color=theme.CORAL_DARK,
            size_hint_y=None,
            height=dp(20),
            halign="left",
        )
        title.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        card.add_widget(title)
        body = WrappedLabel(
            text="点一下任务，可以修改名字、星星数量和重复时间。每天的任务会在零点重新开始。",
            font_size=theme.FS_TINY,
            color=theme.MUTED,
            size_hint_y=None,
        )
        card.add_widget(body)
        return card
