from __future__ import annotations

from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget

from .. import theme
from ..ui.widgets import Card, PhotoCard, PrimaryButton, WrappedLabel
from .base import PageScreen


class AlbumScreen(PageScreen):
    def rebuild(self):
        self.content.clear_widgets()
        self.add(self.brand_bar())
        self.add(self.page_title("成长相册", "把长大的瞬间，留在手心里"))
        self.add(self._toolbar())
        if not self.state.photos:
            self.add(self._empty())
        else:
            for group in self.state.photo_groups:
                self.add(self._month_header(group["label"], len(group["photos"])))
                self.add(self._grid(group["photos"]))
        note = Label(
            text="照片保存在本机；卸载 App 会一并删除。",
            font_name=theme.FONT_CN,
            font_size=theme.FS_TINY,
            color=theme.MUTED,
            size_hint_y=None,
            height=dp(30),
            halign="center",
            valign="middle",
        )
        note.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        self.add(note)

    def _toolbar(self):
        row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(46),
            spacing=dp(8),
        )
        count = Label(
            text=f"共 {self.state.photo_count} 张 · 只保存在本机",
            font_name=theme.FONT_CN,
            font_size=theme.FS_SMALL,
            color=theme.MUTED,
            halign="left",
            valign="middle",
            size_hint_x=1,
        )
        count.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        row.add_widget(count)
        add = PrimaryButton(
            text="＋ 添加照片",
            size_hint=(None, None),
            width=dp(132),
            height=dp(40),
            font_size=theme.FS_SMALL,
            radius=dp(13),
        )
        add.bind(on_release=lambda *_: self.app.pick_photo())
        row.add_widget(add)
        return row

    def _month_header(self, label: str, count: int):
        row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(28),
            spacing=dp(8),
        )
        title = Label(
            text=label,
            font_name=theme.FONT_CN_BOLD,
            font_size=theme.FS_SECTION,
            color=theme.INK,
            halign="left",
            valign="middle",
            size_hint_x=1,
        )
        title.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        row.add_widget(title)
        badge = Label(
            text=f"{count} 张",
            font_name=theme.FONT_CN,
            font_size=theme.FS_TINY,
            color=theme.MUTED,
            size_hint=(None, None),
            size=(dp(48), dp(22)),
            halign="right",
            valign="middle",
        )
        row.add_widget(badge)
        return row

    def _grid(self, photos):
        grid = GridLayout(
            cols=2,
            size_hint_y=None,
            spacing=dp(10),
            row_default_height=dp(212),
            row_force_default=True,
            height=dp(212),
        )
        grid.bind(minimum_height=grid.setter("height"))
        for photo in photos:
            card = PhotoCard(
                size_hint=(1, None),
                height=dp(212),
                photo=photo,
                thumb_path=self.state.repo.photo_path(photo, thumb=True),
                caption=photo.get("caption", ""),
                date_text=self._date_label(photo.get("taken_on", "")),
            )
            card.bind(on_release=lambda inst, photo=photo: self.app.open_photo(photo))
            grid.add_widget(card)
        return grid

    def _empty(self):
        card = Card(
            orientation="vertical",
            size_hint_y=None,
            height=dp(370),
            padding=[dp(22), dp(24), dp(22), dp(22)],
            spacing=dp(8),
            radius=dp(24),
            bg_color=theme.CARD_SOFT,
        )
        art = Card(
            orientation="vertical",
            size_hint_y=None,
            height=dp(146),
            padding=dp(6),
            radius=dp(18),
            bg_color=theme.CORAL_WASH,
            shadow=False,
        )
        plus = Label(
            text="＋",
            font_name=theme.FONT_CN,
            font_size=sp(46),
            color=theme.CORAL,
            halign="center",
            valign="middle",
        )
        plus.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        art.add_widget(plus)
        card.add_widget(art)
        title = Label(
            text="相册还是空的",
            font_name=theme.FONT_CN_BOLD,
            font_size=theme.FS_BODY,
            color=theme.INK,
            size_hint_y=None,
            height=dp(28),
            halign="center",
        )
        title.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        card.add_widget(title)
        body = WrappedLabel(
            text="拍下今天的小进步，或者从手机相册里选一张。\n每一张都会成为以后翻看的礼物。",
            font_size=theme.FS_SMALL,
            color=theme.MUTED,
            halign="center",
            size_hint_y=None,
        )
        card.add_widget(body)
        card.add_widget(Widget())
        row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(46), spacing=dp(8))
        row.add_widget(Widget())
        button = PrimaryButton(
            text="添加第一张照片",
            size_hint=(None, None),
            width=dp(190),
            height=dp(44),
            font_size=theme.FS_SMALL,
        )
        button.bind(on_release=lambda *_: self.app.pick_photo())
        row.add_widget(button)
        row.add_widget(Widget())
        card.add_widget(row)
        return card

    @staticmethod
    def _date_label(iso: str) -> str:
        try:
            _, month, day = iso.split("-")
            return f"{int(month)}月{int(day)}日"
        except ValueError:
            return iso
