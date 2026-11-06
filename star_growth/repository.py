"""SQLite persistence for the growth diary.

Everything lives in a single SQLite file plus two photo folders inside the
application's private data directory.  There is deliberately no network code in
this module: the diary belongs to the phone it was written on.
"""
from __future__ import annotations

import shutil
import sqlite3
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

try:  # Pillow is available on desktop and in the Android build.
    from PIL import Image, ImageOps
except Exception:  # pragma: no cover - only used on unusual minimal installs
    Image = None
    ImageOps = None


DEFAULT_TASKS = [
    ("自己刷牙", 2, "刷", "#67C4AE"),
    ("读一本绘本", 3, "读", "#FF7A66"),
    ("户外活动 30 分钟", 3, "动", "#6FAEE8"),
    ("收好玩具", 2, "收", "#A68BE0"),
    ("九点前上床", 2, "睡", "#FFC44D"),
]


class RepositoryError(RuntimeError):
    """A user-facing data error."""


class PhotoError(RepositoryError):
    """Raised when an image cannot be imported."""


def today_iso() -> str:
    return date.today().isoformat()


def _clean_text(value: str | None) -> str:
    return (value or "").strip()


class GrowthRepository:
    def __init__(self, data_dir: str | Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.photos_dir = self.data_dir / "photos"
        self.thumbs_dir = self.data_dir / "thumbs"
        self.photos_dir.mkdir(exist_ok=True)
        self.thumbs_dir.mkdir(exist_ok=True)
        self.db_path = self.data_dir / "growth.db"
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self._migrate()
        self._seed_if_needed()

    # ------------------------------------------------------------------
    # Setup & schema
    # ------------------------------------------------------------------
    def _migrate(self) -> None:
        with self.conn:
            self.conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS profile (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    name TEXT NOT NULL DEFAULT '小宝贝',
                    birthday TEXT,
                    avatar TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    points INTEGER NOT NULL DEFAULT 1,
                    icon TEXT NOT NULL DEFAULT '星',
                    color TEXT NOT NULL DEFAULT '#FF7A66',
                    schedule TEXT NOT NULL DEFAULT 'daily',
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS completions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER NOT NULL,
                    task_title TEXT NOT NULL,
                    date TEXT NOT NULL,
                    points INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(task_id, date)
                );
                CREATE TABLE IF NOT EXISTS point_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    delta INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    ref_type TEXT,
                    ref_id INTEGER,
                    date TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS photos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    thumbname TEXT NOT NULL,
                    caption TEXT NOT NULL DEFAULT '',
                    taken_on TEXT NOT NULL,
                    width INTEGER NOT NULL DEFAULT 0,
                    height INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_completions_date
                    ON completions(date);
                CREATE INDEX IF NOT EXISTS idx_events_date
                    ON point_events(date);
                CREATE INDEX IF NOT EXISTS idx_events_ref
                    ON point_events(ref_type, ref_id);
                CREATE INDEX IF NOT EXISTS idx_photos_taken
                    ON photos(taken_on);
                """
            )
            self.conn.execute(
                "INSERT OR IGNORE INTO profile(id, name, created_at) VALUES (1, ?, ?)",
                ("小宝贝", datetime.now().isoformat(timespec="seconds")),
            )
        self.conn.execute("PRAGMA user_version=1")

    def _seed_if_needed(self) -> None:
        row = self.conn.execute(
            "SELECT value FROM meta WHERE key='seeded'"
        ).fetchone()
        if row:
            return
        with self.conn:
            count = self.conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
            if count == 0:
                now = datetime.now().isoformat(timespec="seconds")
                for order, (title, points, icon, color) in enumerate(DEFAULT_TASKS):
                    self.conn.execute(
                        """INSERT INTO tasks
                           (title, points, icon, color, schedule, sort_order, created_at)
                           VALUES (?, ?, ?, ?, 'daily', ?, ?)""",
                        (title, points, icon, color, order, now),
                    )
            self.conn.execute(
                "INSERT OR REPLACE INTO meta(key, value) VALUES ('seeded', '1')"
            )

    # ------------------------------------------------------------------
    # Profile
    # ------------------------------------------------------------------
    def get_profile(self) -> dict[str, Any]:
        row = self.conn.execute("SELECT * FROM profile WHERE id=1").fetchone()
        return dict(row) if row else {
            "id": 1,
            "name": "小宝贝",
            "birthday": None,
            "avatar": None,
        }

    def update_profile(
        self,
        name: str,
        birthday: str | None = None,
    ) -> dict[str, Any]:
        name = _clean_text(name)
        if not name:
            raise RepositoryError("名字不能为空")
        if len(name) > 20:
            raise RepositoryError("名字最多 20 个字")
        if birthday:
            try:
                date.fromisoformat(birthday)
            except ValueError as exc:
                raise RepositoryError("生日格式应为 YYYY-MM-DD") from exc
        else:
            birthday = None
        with self.conn:
            self.conn.execute(
                "UPDATE profile SET name=?, birthday=? WHERE id=1",
                (name, birthday),
            )
        return self.get_profile()

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------
    @staticmethod
    def _task(row: sqlite3.Row) -> dict[str, Any]:
        item = dict(row)
        item["active"] = bool(item.get("active", 1))
        return item

    def list_tasks(self, active_only: bool = True) -> list[dict[str, Any]]:
        sql = "SELECT * FROM tasks"
        args: tuple[Any, ...] = ()
        if active_only:
            sql += " WHERE active=1"
        sql += " ORDER BY sort_order, id"
        return [self._task(row) for row in self.conn.execute(sql, args)]

    def get_task(self, task_id: int) -> dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT * FROM tasks WHERE id=?", (task_id,)
        ).fetchone()
        return self._task(row) if row else None

    def create_task(
        self,
        title: str,
        points: int,
        icon: str = "星",
        color: str = "#FF7A66",
        schedule: str = "daily",
    ) -> dict[str, Any]:
        title = _clean_text(title)
        if not title:
            raise RepositoryError("任务名称不能为空")
        if len(title) > 24:
            raise RepositoryError("任务名称最多 24 个字")
        points = int(points)
        if not 1 <= points <= 99:
            raise RepositoryError("积分需要在 1 到 99 之间")
        if schedule not in ("daily", "weekdays", "weekend"):
            raise RepositoryError("未知的重复方式")
        with self.conn:
            max_order = self.conn.execute(
                "SELECT COALESCE(MAX(sort_order), -1) FROM tasks"
            ).fetchone()[0]
            cur = self.conn.execute(
                """INSERT INTO tasks
                   (title, points, icon, color, schedule, sort_order, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    title,
                    points,
                    _clean_text(icon)[:2] or "星",
                    color,
                    schedule,
                    max_order + 1,
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
            task_id = cur.lastrowid
        return self.get_task(task_id)

    def update_task(
        self,
        task_id: int,
        title: str,
        points: int,
        icon: str,
        color: str,
        schedule: str,
    ) -> dict[str, Any]:
        title = _clean_text(title)
        if not title:
            raise RepositoryError("任务名称不能为空")
        if len(title) > 24:
            raise RepositoryError("任务名称最多 24 个字")
        points = int(points)
        if not 1 <= points <= 99:
            raise RepositoryError("积分需要在 1 到 99 之间")
        if schedule not in ("daily", "weekdays", "weekend"):
            raise RepositoryError("未知的重复方式")
        with self.conn:
            self.conn.execute(
                """UPDATE tasks SET title=?, points=?, icon=?, color=?,
                   schedule=? WHERE id=?""",
                (
                    title,
                    points,
                    _clean_text(icon)[:2] or "星",
                    color,
                    schedule,
                    task_id,
                ),
            )
        task = self.get_task(task_id)
        if not task:
            raise RepositoryError("任务不存在")
        return task

    def delete_task(self, task_id: int, on_date: str | None = None) -> None:
        """Delete a task and revoke a completion earned *on that date*.

        Historical completions are intentionally preserved: they are part of
        the child's record even if the family later removes the habit.
        """
        on_date = on_date or today_iso()
        with self.conn:
            row = self.conn.execute(
                "SELECT id FROM completions WHERE task_id=? AND date=?",
                (task_id, on_date),
            ).fetchone()
            if row:
                completion_id = row["id"]
                self.conn.execute(
                    "DELETE FROM point_events WHERE ref_type='completion' AND ref_id=?",
                    (completion_id,),
                )
                self.conn.execute(
                    "DELETE FROM completions WHERE id=?", (completion_id,)
                )
            self.conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))

    def reorder_task(self, task_id: int, direction: int) -> None:
        """Move a task up (-1) or down (+1) in the list."""
        tasks = self.list_tasks()
        ids = [task["id"] for task in tasks]
        if task_id not in ids:
            return
        index = ids.index(task_id)
        target = index + direction
        if not 0 <= target < len(ids):
            return
        ids[index], ids[target] = ids[target], ids[index]
        with self.conn:
            for order, item_id in enumerate(ids):
                self.conn.execute(
                    "UPDATE tasks SET sort_order=? WHERE id=?", (order, item_id)
                )

    @staticmethod
    def _schedule_matches(schedule: str, day: date) -> bool:
        if schedule == "weekdays":
            return day.weekday() < 5
        if schedule == "weekend":
            return day.weekday() >= 5
        return True

    def tasks_for_date(self, on_date: str) -> list[dict[str, Any]]:
        day = date.fromisoformat(on_date)
        tasks = [
            task
            for task in self.list_tasks()
            if self._schedule_matches(task["schedule"], day)
        ]
        completed = {
            row["task_id"]: dict(row)
            for row in self.conn.execute(
                "SELECT * FROM completions WHERE date=?", (on_date,)
            )
        }
        for task in tasks:
            completion = completed.get(task["id"])
            task["done"] = completion is not None
            task["completion_id"] = completion["id"] if completion else None
            task["awarded_points"] = (
                completion["points"] if completion else task["points"]
            )
        return tasks

    # ------------------------------------------------------------------
    # Completions & points
    # ------------------------------------------------------------------
    def toggle_completion(self, task_id: int, on_date: str | None = None) -> dict[str, Any]:
        on_date = on_date or today_iso()
        task = self.get_task(task_id)
        if not task:
            raise RepositoryError("任务不存在")
        now = datetime.now().isoformat(timespec="seconds")
        row = self.conn.execute(
            "SELECT * FROM completions WHERE task_id=? AND date=?",
            (task_id, on_date),
        ).fetchone()
        with self.conn:
            if row:
                completion_id = row["id"]
                self.conn.execute(
                    "DELETE FROM point_events WHERE ref_type='completion' AND ref_id=?",
                    (completion_id,),
                )
                self.conn.execute(
                    "DELETE FROM completions WHERE id=?", (completion_id,)
                )
                return {
                    "done": False,
                    "delta": -int(row["points"]),
                    "points": int(row["points"]),
                    "title": task["title"],
                }
            cur = self.conn.execute(
                """INSERT INTO completions
                   (task_id, task_title, date, points, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (task_id, task["title"], on_date, int(task["points"]), now),
            )
            completion_id = cur.lastrowid
            self.conn.execute(
                """INSERT INTO point_events
                   (delta, reason, ref_type, ref_id, date, created_at)
                   VALUES (?, ?, 'completion', ?, ?, ?)""",
                (
                    int(task["points"]),
                    f"完成「{task['title']}」",
                    completion_id,
                    on_date,
                    now,
                ),
            )
        return {
            "done": True,
            "delta": int(task["points"]),
            "points": int(task["points"]),
            "title": task["title"],
        }

    def total_points(self) -> int:
        return int(
            self.conn.execute(
                "SELECT COALESCE(SUM(delta), 0) FROM point_events"
            ).fetchone()[0]
        )

    def points_on(self, on_date: str) -> int:
        return int(
            self.conn.execute(
                "SELECT COALESCE(SUM(delta), 0) FROM point_events WHERE date=?",
                (on_date,),
            ).fetchone()[0]
        )

    def points_between(self, start: str, end: str) -> int:
        return int(
            self.conn.execute(
                """SELECT COALESCE(SUM(delta), 0) FROM point_events
                   WHERE date BETWEEN ? AND ?""",
                (start, end),
            ).fetchone()[0]
        )

    def week_points(self, anchor: date | None = None) -> list[dict[str, Any]]:
        anchor = anchor or date.today()
        monday = anchor - timedelta(days=anchor.weekday())
        labels = ["一", "二", "三", "四", "五", "六", "日"]
        result = []
        for offset in range(7):
            day = monday + timedelta(days=offset)
            iso = day.isoformat()
            result.append(
                {
                    "date": iso,
                    "label": labels[offset],
                    "value": self.points_on(iso),
                    "is_today": day == anchor,
                    "is_future": day > anchor,
                }
            )
        return result

    def completion_count(self, on_date: str | None = None) -> int:
        if on_date:
            return int(
                self.conn.execute(
                    "SELECT COUNT(*) FROM completions WHERE date=?", (on_date,)
                ).fetchone()[0]
            )
        return int(
            self.conn.execute("SELECT COUNT(*) FROM completions").fetchone()[0]
        )

    def streak(self, anchor: date | None = None) -> int:
        anchor = anchor or date.today()
        rows = self.conn.execute(
            "SELECT DISTINCT date FROM completions WHERE date<=? ORDER BY date DESC",
            (anchor.isoformat(),),
        ).fetchall()
        days = {row["date"] for row in rows}
        cursor = anchor
        if cursor.isoformat() not in days:
            cursor -= timedelta(days=1)
        streak = 0
        while cursor.isoformat() in days:
            streak += 1
            cursor -= timedelta(days=1)
        return streak

    def recent_events(self, limit: int = 40) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """SELECT * FROM point_events
               ORDER BY created_at DESC, id DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # Photos
    # ------------------------------------------------------------------
    def _photo_name(self, taken_on: str) -> str:
        return f"{taken_on.replace('-', '')}_{uuid.uuid4().hex[:10]}"

    def add_photo(
        self,
        source_path: str | Path,
        caption: str = "",
        taken_on: str | None = None,
    ) -> dict[str, Any]:
        source = Path(source_path)
        if not source.exists() or not source.is_file():
            raise PhotoError("找不到这张照片")
        taken_on = taken_on or today_iso()
        try:
            date.fromisoformat(taken_on)
        except ValueError as exc:
            raise PhotoError("照片日期格式不正确") from exc
        caption = _clean_text(caption)[:60]
        stem = self._photo_name(taken_on)
        if Image is None:
            filename = stem + source.suffix.lower()
            thumbname = filename
            shutil.copyfile(source, self.photos_dir / filename)
            shutil.copyfile(source, self.thumbs_dir / filename)
            width = height = 0
        else:
            try:
                with Image.open(source) as opened:
                    image = ImageOps.exif_transpose(opened)
                    width, height = image.size
                    if image.mode not in ("RGB", "L"):
                        background = Image.new("RGB", image.size, (255, 255, 255))
                        if image.mode == "RGBA":
                            background.paste(image, mask=image.getchannel("A"))
                        else:
                            background.paste(image.convert("RGBA"), mask=image.convert("RGBA").getchannel("A"))
                        image = background
                    elif image.mode == "L":
                        image = image.convert("RGB")
                    filename = stem + ".jpg"
                    thumbname = filename
                    image.save(
                        self.photos_dir / filename,
                        "JPEG",
                        quality=92,
                        optimize=True,
                    )
                    thumb = image.copy()
                    thumb.thumbnail((900, 900), Image.Resampling.LANCZOS)
                    thumb.save(
                        self.thumbs_dir / thumbname,
                        "JPEG",
                        quality=86,
                        optimize=True,
                    )
            except Exception as exc:
                raise PhotoError("无法读取这张图片，请换一张试试") from exc
        now = datetime.now().isoformat(timespec="seconds")
        with self.conn:
            cur = self.conn.execute(
                """INSERT INTO photos
                   (filename, thumbname, caption, taken_on, width, height, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (filename, thumbname, caption, taken_on, width, height, now),
            )
            photo_id = cur.lastrowid
        return self.get_photo(photo_id)

    def get_photo(self, photo_id: int) -> dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT * FROM photos WHERE id=?", (photo_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_photos(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM photos ORDER BY taken_on DESC, created_at DESC, id DESC"
        ).fetchall()
        return [dict(row) for row in rows]

    def photo_count(self) -> int:
        return int(self.conn.execute("SELECT COUNT(*) FROM photos").fetchone()[0])

    def photo_path(self, photo: dict[str, Any], thumb: bool = False) -> str:
        folder = self.thumbs_dir if thumb else self.photos_dir
        key = "thumbname" if thumb else "filename"
        return str(folder / photo[key])

    def delete_photo(self, photo_id: int) -> None:
        photo = self.get_photo(photo_id)
        if not photo:
            return
        with self.conn:
            self.conn.execute("DELETE FROM photos WHERE id=?", (photo_id,))
        for folder, key in ((self.photos_dir, "filename"), (self.thumbs_dir, "thumbname")):
            try:
                (folder / photo[key]).unlink(missing_ok=True)
            except OSError:
                pass

    # ------------------------------------------------------------------
    # Maintenance
    # ------------------------------------------------------------------
    def reset_all(self) -> None:
        with self.conn:
            self.conn.execute("DELETE FROM point_events")
            self.conn.execute("DELETE FROM completions")
            self.conn.execute("DELETE FROM photos")
            self.conn.execute("DELETE FROM tasks")
            self.conn.execute("DELETE FROM profile")
            self.conn.execute("DELETE FROM meta")
            self.conn.execute(
                "INSERT INTO profile(id, name, created_at) VALUES (1, ?, ?)",
                ("小宝贝", datetime.now().isoformat(timespec="seconds")),
            )
            self.conn.execute(
                "INSERT INTO meta(key, value) VALUES ('seeded', '1')"
            )
            now = datetime.now().isoformat(timespec="seconds")
            for order, (title, points, icon, color) in enumerate(DEFAULT_TASKS):
                self.conn.execute(
                    """INSERT INTO tasks
                       (title, points, icon, color, schedule, sort_order, created_at)
                       VALUES (?, ?, ?, ?, 'daily', ?, ?)""",
                    (title, points, icon, color, order, now),
                )
        for folder in (self.photos_dir, self.thumbs_dir):
            for child in folder.iterdir():
                if child.is_file():
                    try:
                        child.unlink()
                    except OSError:
                        pass

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass
