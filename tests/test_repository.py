from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from star_growth.repository import GrowthRepository, PhotoError, RepositoryError


@pytest.fixture()
def repo(tmp_path: Path):
    store = GrowthRepository(tmp_path / "data")
    yield store
    store.close()


def test_first_run_has_default_tasks(repo: GrowthRepository):
    tasks = repo.list_tasks()
    assert len(tasks) == 5
    assert repo.get_profile()["name"] == "小宝贝"
    assert repo.total_points() == 0


def test_toggle_completion_awards_and_revokes_points(repo: GrowthRepository):
    task = repo.list_tasks()[0]
    day = date.today().isoformat()

    result = repo.toggle_completion(task["id"], day)
    assert result == {
        "done": True,
        "delta": task["points"],
        "points": task["points"],
        "title": task["title"],
    }
    assert repo.total_points() == task["points"]
    assert repo.points_on(day) == task["points"]
    assert repo.tasks_for_date(day)[0]["done"] is True
    assert repo.recent_events()[0]["reason"] == f"完成「{task['title']}」"

    undo = repo.toggle_completion(task["id"], day)
    assert undo["done"] is False
    assert undo["delta"] == -task["points"]
    assert repo.total_points() == 0
    assert repo.recent_events() == []


def test_points_history_week_and_streak(repo: GrowthRepository):
    task = repo.list_tasks()[0]
    today = date.today()
    yesterday = today - timedelta(days=1)

    repo.toggle_completion(task["id"], today.isoformat())
    repo.toggle_completion(task["id"], yesterday.isoformat())

    assert repo.total_points() == task["points"] * 2
    assert repo.streak(today) == 2
    assert repo.completion_count() == 2
    week = repo.week_points(today)
    assert len(week) == 7
    assert sum(item["value"] for item in week) == task["points"] * 2


def test_streak_survives_a_not_yet_finished_today(repo: GrowthRepository):
    task = repo.list_tasks()[0]
    yesterday = date.today() - timedelta(days=1)
    repo.toggle_completion(task["id"], yesterday.isoformat())
    assert repo.streak(date.today()) == 1


def test_schedule_filtering(repo: GrowthRepository):
    weekday_task = repo.create_task(
        "上幼儿园", 2, "读", "#6FAEE8", "weekdays"
    )
    weekend_task = repo.create_task(
        "去公园", 3, "动", "#67C4AE", "weekend"
    )
    monday = date(2026, 11, 2)
    saturday = date(2026, 11, 7)

    monday_titles = {item["title"] for item in repo.tasks_for_date(monday.isoformat())}
    saturday_titles = {item["title"] for item in repo.tasks_for_date(saturday.isoformat())}
    assert weekday_task["title"] in monday_titles
    assert weekend_task["title"] not in monday_titles
    assert weekend_task["title"] in saturday_titles
    assert weekday_task["title"] not in saturday_titles


def test_delete_task_revokes_only_todays_points(repo: GrowthRepository):
    task = repo.list_tasks()[0]
    today = date.today()
    yesterday = today - timedelta(days=1)
    repo.toggle_completion(task["id"], yesterday.isoformat())
    repo.toggle_completion(task["id"], today.isoformat())
    assert repo.total_points() == task["points"] * 2

    repo.delete_task(task["id"], today.isoformat())
    assert repo.total_points() == task["points"]
    assert repo.points_on(today.isoformat()) == 0
    assert repo.points_on(yesterday.isoformat()) == task["points"]
    assert task["id"] not in [item["id"] for item in repo.list_tasks()]


def test_profile_validation(repo: GrowthRepository):
    updated = repo.update_profile("小满", "2021-03-18")
    assert updated["name"] == "小满"
    assert updated["birthday"] == "2021-03-18"

    with pytest.raises(RepositoryError):
        repo.update_profile("", None)
    with pytest.raises(RepositoryError):
        repo.update_profile("小满", "18/03/2021")


def test_task_validation(repo: GrowthRepository):
    with pytest.raises(RepositoryError):
        repo.create_task("", 2)
    with pytest.raises(RepositoryError):
        repo.create_task("刷牙", 0)
    with pytest.raises(RepositoryError):
        repo.create_task("刷牙", 100)
    with pytest.raises(RepositoryError):
        repo.create_task("刷牙", 2, schedule="monthly")


def test_photo_copy_thumbnail_and_delete(repo: GrowthRepository, tmp_path: Path):
    source = tmp_path / "source.png"
    image = Image.new("RGB", (1200, 800), (250, 230, 210))
    draw = ImageDraw.Draw(image)
    draw.ellipse((300, 100, 900, 700), fill=(255, 122, 102))
    image.save(source)

    photo = repo.add_photo(source, "第一次自己穿鞋", "2026-11-06")
    assert photo["width"] == 1200
    assert photo["height"] == 800
    assert repo.photo_count() == 1
    original = Path(repo.photo_path(photo))
    thumb = Path(repo.photo_path(photo, thumb=True))
    assert original.exists() and original.stat().st_size > 0
    assert thumb.exists() and thumb.stat().st_size > 0
    assert original != source

    repo.delete_photo(photo["id"])
    assert repo.photo_count() == 0
    assert not original.exists()
    assert not thumb.exists()


def test_bad_photo_raises(repo: GrowthRepository, tmp_path: Path):
    bad = tmp_path / "not_an_image.txt"
    bad.write_text("hello")
    with pytest.raises(PhotoError):
        repo.add_photo(bad)


def test_reset_restores_initial_state(repo: GrowthRepository):
    task = repo.list_tasks()[0]
    repo.toggle_completion(task["id"])
    repo.update_profile("小满", "2021-03-18")
    repo.reset_all()

    assert repo.get_profile()["name"] == "小宝贝"
    assert repo.total_points() == 0
    assert repo.photo_count() == 0
    assert len(repo.list_tasks()) == 5
