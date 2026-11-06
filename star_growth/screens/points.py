from __future__ import annotations

from kivy.graphics import Color, Ellipse
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget

from .. import theme
from ..ui.widgets import Card, SectionTitle, StarBadge, WeekChart, WrappedLabel
from .base import PageScreen


class StarsHero(Card):
    def __init__(self, state, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(172),
            padding=[dp(20), dp(16)],
            spacing=dp(8),
            radius=dp(26),
            bg_color=theme.HONEY,
            **kwargs,
        )
        with self.canvas.before:
            self._glow_color = Color(1, 1, 1, 0.17)
            self._glow = Ellipse()
            self._glow2_color = Color(1, 1, 1, 0.10)
            self._glow2 = Ellipse()
        self.bind(pos=self._decorate, size=self._decorate)
        self._decorate()
        left = BoxLayout(orientation="vertical", spacing=dp(1))
        eyebrow = Label(
            text="我的星星",
            font_name=theme.FONT_CN,
            font_size=theme.FS_SMALL,
            color=(0.38, 0.26, 0.06, 0.72),
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(22),
        )
        eyebrow.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        left.add_widget(eyebrow)
        value = Label(
            text=f"[size={int(sp(46))}][b]{state.total_points}[/b][/size] [size={int(sp(13))}]颗[/size]",
            font_name=theme.FONT_CN_BOLD,
            font_size=sp(46),
            markup=True,
            color=theme.INK,
            halign="left",
            valign="bottom",
            size_hint_y=None,
            height=dp(64),
        )
        value.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        left.add_widget(value)
        sub = Label(
            text="继续收集，愿望会越来越近",
            font_name=theme.FONT_CN,
            font_size=theme.FS_TINY,
            color=(0.38, 0.26, 0.06, 0.68),
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(22),
        )
        sub.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        left.add_widget(sub)
        self.add_widget(left)

        right = BoxLayout(
            orientation="vertical",
            size_hint=(None, 1),
            width=dp(108),
            spacing=dp(2),
        )
        star = Label(
            text="★",
            font_name=theme.FONT_CN,
            font_size=sp(52),
            color=(1, 1, 1, 0.55),
            size_hint_y=None,
            height=dp(62),
            halign="center",
            valign="middle",
        )
        star.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        right.add_widget(star)
        streak = Label(
            text=f"连续 {state.streak} 天" if state.streak else "从今天开始",
            font_name=theme.FONT_CN_BOLD,
            font_size=theme.FS_TINY,
            color=(0.38, 0.26, 0.06, 0.86),
            size_hint_y=None,
            height=dp(24),
            halign="center",
            valign="middle",
        )
        streak.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        right.add_widget(streak)
        self.add_widget(right)

    def _decorate(self, *_):
        self._glow.pos = (self.right - dp(84), self.y + self.height - dp(86))
        self._glow.size = (dp(150), dp(150))
        self._glow2.pos = (self.right - dp(120), self.y - dp(40))
        self._glow2.size = (dp(100), dp(100))


class HistoryRow(Card):
    def __init__(self, event, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(58),
            padding=[dp(12), dp(8)],
            spacing=dp(9),
            radius=dp(16),
            bg_color=theme.CARD,
            shadow=False,
            **kwargs,
        )
        star = Label(
            text="★",
            font_name=theme.FONT_CN,
            font_size=sp(18),
            color=theme.HONEY,
            size_hint=(None, None),
            size=(dp(26), dp(26)),
            halign="center",
            valign="middle",
        )
        self.add_widget(star)
        text_box = BoxLayout(orientation="vertical", spacing=dp(1))
        reason = Label(
            text=event.get("reason", "完成任务"),
            font_name=theme.FONT_CN,
            font_size=theme.FS_SMALL,
            color=theme.INK,
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(22),
            shorten=True,
            shorten_from="right",
        )
        reason.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        text_box.add_widget(reason)
        time = Label(
            text=event.get("time_text", ""),
            font_name=theme.FONT_CN,
            font_size=theme.FS_TINY,
            color=theme.MUTED,
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(18),
        )
        time.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        text_box.add_widget(time)
        self.add_widget(text_box)
        delta = int(event.get("delta", 0))
        amount = Label(
            text=f"{'+' if delta >= 0 else ''}{delta}",
            font_name=theme.FONT_CN_BOLD,
            font_size=theme.FS_BODY,
            color=theme.HONEY_DARK if delta >= 0 else theme.CORAL_DARK,
            size_hint=(None, None),
            size=(dp(42), dp(26)),
            halign="right",
            valign="middle",
        )
        self.add_widget(amount)


class PointsScreen(PageScreen):
    def rebuild(self):
        self.content.clear_widgets()
        self.add(self.brand_bar())
        self.add(self.page_title("我的星星", "每一颗星，都是成长的小证据"))
        self.add(StarsHero(self.state))
        self.add(self._stats())
        self.add(self._week_card())
        self.add(SectionTitle("星星记录"))
        self._build_history()
        note = Label(
            text="完成任务会自动记录星星，取消完成会收回当天的星星。",
            font_name=theme.FONT_CN,
            font_size=theme.FS_TINY,
            color=theme.MUTED,
            size_hint_y=None,
            height=dp(32),
            halign="center",
            valign="middle",
        )
        note.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        self.add(note)

    def _stats(self):
        row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(88),
            spacing=dp(8),
        )
        values = [
            (f"+{self.state.today_points}", "今天"),
            (f"+{self.state.week_points_total}", "本周"),
            (str(self.state.completion_total), "完成次数"),
        ]
        for index, (value, label) in enumerate(values):
            card = Card(
                orientation="vertical",
                size_hint_x=1,
                padding=[dp(6), dp(10)],
                spacing=dp(1),
                radius=dp(16),
                bg_color=theme.CARD_SOFT if index != 1 else theme.CORAL_WASH,
                shadow=False,
            )
            number = Label(
                text=value,
                font_name=theme.FONT_CN_BOLD,
                font_size=sp(22),
                color=theme.INK if index != 1 else theme.CORAL_DARK,
                size_hint_y=None,
                height=dp(34),
                halign="center",
                valign="middle",
            )
            number.bind(size=lambda inst, val: setattr(inst, "text_size", val))
            card.add_widget(number)
            caption = Label(
                text=label,
                font_name=theme.FONT_CN,
                font_size=theme.FS_TINY,
                color=theme.MUTED,
                size_hint_y=None,
                height=dp(20),
                halign="center",
                valign="middle",
            )
            caption.bind(size=lambda inst, val: setattr(inst, "text_size", val))
            card.add_widget(caption)
            row.add_widget(card)
        return row

    def _week_card(self):
        card = Card(
            orientation="vertical",
            size_hint_y=None,
            height=dp(224),
            padding=[dp(16), dp(14)],
            spacing=dp(4),
            radius=dp(22),
            bg_color=theme.CARD,
        )
        header = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(26))
        title = Label(
            text="这一周",
            font_name=theme.FONT_CN_BOLD,
            font_size=theme.FS_SECTION,
            color=theme.INK,
            halign="left",
            valign="middle",
            size_hint_x=1,
        )
        title.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        header.add_widget(title)
        total = self.state.week_points_total
        badge = Label(
            text=f"共 +{total} 颗",
            font_name=theme.FONT_CN,
            font_size=theme.FS_TINY,
            color=theme.CORAL_DARK,
            size_hint=(None, None),
            size=(dp(76), dp(22)),
            halign="right",
            valign="middle",
        )
        header.add_widget(badge)
        card.add_widget(header)
        today_index = next(
            (index for index, item in enumerate(self.state.week) if item.get("is_today")),
            -1,
        )
        chart = WeekChart(
            values=[item["value"] for item in self.state.week],
            labels=[item["label"] for item in self.state.week],
            today_index=today_index,
            size_hint_y=None,
            height=dp(154),
        )
        card.add_widget(chart)
        return card

    def _build_history(self):
        if not self.state.history:
            card = Card(
                orientation="vertical",
                size_hint_y=None,
                height=dp(146),
                padding=[dp(16), dp(18)],
                spacing=dp(3),
                radius=dp(20),
                bg_color=theme.CARD_SOFT,
                shadow=False,
            )
            card.add_widget(Widget())
            star = StarBadge(text="★", font_size=sp(28), color=theme.HONEY, size=(dp(36), dp(36)))
            star.pos_hint = {"center_x": 0.5}
            card.add_widget(star)
            title = Label(
                text="还没有记录",
                font_name=theme.FONT_CN_BOLD,
                font_size=theme.FS_BODY,
                color=theme.INK,
                size_hint_y=None,
                height=dp(26),
                halign="center",
            )
            title.bind(size=lambda inst, val: setattr(inst, "text_size", val))
            card.add_widget(title)
            body = WrappedLabel(
                text="完成第一件小事，第一颗星就会亮起来。",
                font_size=theme.FS_SMALL,
                color=theme.MUTED,
                halign="center",
                size_hint_y=None,
            )
            card.add_widget(body)
            card.add_widget(Widget())
            self.add(card)
            return
        for event in self.state.history[:30]:
            self.add(HistoryRow(event))
