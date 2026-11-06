"""Observable application state.

Every write goes through this object.  It refreshes the derived values and
dispatches one ``on_change`` event, which is what makes all four screens update
at the same instant without any manual refresh button.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from kivy.event import EventDispatcher

from .repository import GrowthRepository, RepositoryError


WEEKDAY_CN = ["一", "二", "三", "四", "五", "六", "日"]
MONTH_CN = [
    "一月",
    "二月",
    "三月",
    "四月",
    "五月",
    "六月",
    "七月",
    "八月",
    "九月",
    "十月",
    "十一月",
    "十二月",
]


def age_from_birthday(birthday: str | None, anchor: date | None = None) -> str:
    if not birthday:
        return "每一天都在长大"
    anchor = anchor or date.today()
    try:
        born = date.fromisoformat(birthday)
    except ValueError:
        return "每一天都在长大"
    months = (anchor.year - born.year) * 12 + (anchor.month - born.month)
    if anchor.day < born.day:
        months -= 1
    months = max(0, months)
    years, rest = divmod(months, 12)
    if years and rest:
        return f"{years} 岁 {rest} 个月"
    if years:
        return f"{years} 岁"
    if months:
        return f"{months} 个月"
    return "刚刚来到这个世界"


def friendly_time(timestamp: str, anchor: date | None = None) -> str:
    anchor = anchor or date.today()
    try:
        moment = datetime.fromisoformat(timestamp)
    except (TypeError, ValueError):
        return ""
    if moment.date() == anchor:
        return f"今天 {moment:%H:%M}"
    if moment.date() == anchor - timedelta(days=1):
        return f"昨天 {moment:%H:%M}"
    if moment.year == anchor.year:
        return f"{moment.month}月{moment.day}日"
    return f"{moment.year}年{moment.month}月{moment.day}日"


class AppState(EventDispatcher):
    __events__ = ("on_change",)

    def __init__(self, repository: GrowthRepository):
        super().__init__()
        self.repo = repository
        self.today = date.today()
        self.profile: dict[str, Any] = {}
        self.tasks: list[dict[str, Any]] = []
        self.today_tasks: list[dict[str, Any]] = []
        self.photos: list[dict[str, Any]] = []
        self.photo_groups: list[dict[str, Any]] = []
        self.history: list[dict[str, Any]] = []
        self.week: list[dict[str, Any]] = []
        self.name = "小宝贝"
        self.birthday: str | None = None
        self.age_text = "每一天都在长大"
        self.total_points = 0
        self.today_points = 0
        self.today_done = 0
        self.today_total = 0
        self.today_possible = 0
        self.progress = 0.0
        self.all_done = False
        self.today_message = ""
        self.week_points_total = 0
        self.completion_total = 0
        self.photo_count = 0
        self.streak = 0
        self.greeting = "你好"
        self.date_text = ""
        self.month_text = ""
        self.load()

    # ------------------------------------------------------------------
    # Derived data
    # ------------------------------------------------------------------
    def load(self) -> None:
        self.today = date.today()
        self.today_iso = self.today.isoformat()
        self.profile = self.repo.get_profile()
        self.name = self.profile.get("name") or "小宝贝"
        self.birthday = self.profile.get("birthday")
        self.age_text = age_from_birthday(self.birthday, self.today)
        self.tasks = self.repo.list_tasks()
        self.today_tasks = self.repo.tasks_for_date(self.today_iso)
        self.total_points = max(0, self.repo.total_points())
        self.today_points = self.repo.points_on(self.today_iso)
        self.today_done = sum(1 for task in self.today_tasks if task.get("done"))
        self.today_total = len(self.today_tasks)
        self.today_possible = sum(int(task["points"]) for task in self.today_tasks)
        self.progress = (
            self.today_done / self.today_total if self.today_total else 0.0
        )
        self.all_done = bool(self.today_tasks) and self.today_done == self.today_total
        self.today_message = self._message()
        self.week = self.repo.week_points(self.today)
        self.week_points_total = sum(int(item["value"]) for item in self.week)
        self.completion_total = self.repo.completion_count()
        self.streak = self.repo.streak(self.today)
        self.photo_count = self.repo.photo_count()
        self.photos = self.repo.list_photos()
        self.photo_groups = self._group_photos(self.photos)
        raw_history = self.repo.recent_events(60)
        self.history = []
        for event in raw_history:
            item = dict(event)
            item["time_text"] = friendly_time(item["created_at"], self.today)
            self.history.append(item)
        hour = datetime.now().hour
        if 5 <= hour < 11:
            self.greeting = "早上好"
        elif 11 <= hour < 13:
            self.greeting = "中午好"
        elif 13 <= hour < 18:
            self.greeting = "下午好"
        else:
            self.greeting = "晚上好"
        self.date_text = (
            f"{self.today.month}月{self.today.day}日 · 周"
            f"{WEEKDAY_CN[self.today.weekday()]}"
        )
        self.month_text = f"{self.today.year}年{MONTH_CN[self.today.month - 1]}"

    def _message(self) -> str:
        if not self.today_tasks:
            return "今天还没有安排任务，先设一个小目标吧"
        if self.today_done == 0:
            return "今天想先完成哪一件小事？"
        if self.all_done:
            return "今天的任务全部点亮，太棒了！"
        remaining = self.today_total - self.today_done
        return f"再完成 {remaining} 件，就集满今天的小星星"

    @staticmethod
    def _group_photos(photos: list[dict[str, Any]]) -> list[dict[str, Any]]:
        groups: list[dict[str, Any]] = []
        for photo in photos:
            key = (photo.get("taken_on") or "")[:7]
            if not groups or groups[-1]["key"] != key:
                try:
                    year, month = key.split("-")
                    label = f"{int(year)}年{int(month)}月"
                except ValueError:
                    label = "更早"
                groups.append({"key": key, "label": label, "photos": []})
            groups[-1]["photos"].append(photo)
        return groups

    def refresh(self) -> None:
        self.load()
        self.dispatch("on_change")

    def on_change(self) -> None:
        """Default no-op so binding always works."""

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------
    def toggle_task(self, task_id: int) -> dict[str, Any]:
        result = self.repo.toggle_completion(task_id, self.today_iso)
        self.refresh()
        return result

    def add_task(self, **values) -> dict[str, Any]:
        task = self.repo.create_task(**values)
        self.refresh()
        return task

    def edit_task(self, task_id: int, **values) -> dict[str, Any]:
        task = self.repo.update_task(task_id, **values)
        self.refresh()
        return task

    def remove_task(self, task_id: int) -> None:
        self.repo.delete_task(task_id, self.today_iso)
        self.refresh()

    def move_task(self, task_id: int, direction: int) -> None:
        self.repo.reorder_task(task_id, direction)
        self.refresh()

    def add_photo(
        self,
        source: str | Path,
        caption: str = "",
        taken_on: str | None = None,
    ) -> dict[str, Any]:
        photo = self.repo.add_photo(source, caption, taken_on or self.today_iso)
        self.refresh()
        return photo

    def remove_photo(self, photo_id: int) -> None:
        self.repo.delete_photo(photo_id)
        self.refresh()

    def save_profile(self, name: str, birthday: str | None) -> None:
        self.profile = self.repo.update_profile(name, birthday)
        self.refresh()

    def reset_all(self) -> None:
        self.repo.reset_all()
        self.refresh()


__all__ = [
    "AppState",
    "RepositoryError",
    "age_from_birthday",
    "friendly_time",
    "MONTH_CN",
    "WEEKDAY_CN",
]
