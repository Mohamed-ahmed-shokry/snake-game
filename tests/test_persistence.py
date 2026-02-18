import json
from pathlib import Path

from snake_game.config import GraphicsSettings, UserSettings
from snake_game.persistence import (
    SAVE_SCHEMA_VERSION,
    best_score_for_settings,
    PersistentData,
    is_new_high_score,
    leaderboard_key,
    load_persistent_data,
    record_score,
    save_persistent_data,
    update_run_stats,
)
from snake_game.types import Difficulty, MapMode, ThemeId


def test_record_score_sorts_and_trims() -> None:
    data = PersistentData(settings=UserSettings(), leaderboard={})
    settings = UserSettings(difficulty=Difficulty.HARD, map_mode=MapMode.WRAP, obstacles_enabled=True)

    for score in [10, 4, 7, 18, 2]:
        record_score(data, settings, score, limit=3)

    key = leaderboard_key(settings)
    assert data.leaderboard[key] == [18, 10, 7]


def test_save_and_load_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "save.json"
    data = PersistentData(
        settings=UserSettings(
            difficulty=Difficulty.EASY,
            map_mode=MapMode.WRAP,
            obstacles_enabled=True,
            muted=True,
        ),
        graphics=GraphicsSettings(
            theme_id=ThemeId.SUNSET,
            ui_scale=1.25,
            show_grid=False,
            reduced_motion=True,
            colorblind_mode="deuteranopia",
        ),
        leaderboard={"easy|wrap|obs": [9, 7, 4]},
        onboarding_seen=True,
    )

    save_persistent_data(data, path)
    loaded = load_persistent_data(path)

    assert loaded.settings.difficulty == Difficulty.EASY
    assert loaded.settings.map_mode == MapMode.WRAP
    assert loaded.settings.obstacles_enabled is True
    assert loaded.settings.muted is True
    assert loaded.graphics.theme_id == ThemeId.SUNSET
    assert loaded.graphics.ui_scale == 1.25
    assert loaded.graphics.show_grid is False
    assert loaded.graphics.reduced_motion is True
    assert loaded.graphics.colorblind_mode == "deuteranopia"
    assert loaded.onboarding_seen is True
    assert loaded.leaderboard["easy|wrap|obs"] == [9, 7, 4]
    assert loaded.schema_version == SAVE_SCHEMA_VERSION


def test_corrupt_file_falls_back_to_defaults(tmp_path: Path) -> None:
    path = tmp_path / "save.json"
    path.write_text("{not-json", encoding="utf-8")

    loaded = load_persistent_data(path)

    assert loaded.settings == UserSettings()
    assert loaded.leaderboard == {}


def test_is_new_high_score_behavior() -> None:
    assert is_new_high_score([], 5) is True
    assert is_new_high_score([10, 8, 6], 11) is True
    assert is_new_high_score([10, 8, 6], 10) is False
    assert is_new_high_score([10, 8, 6], 0) is False


def test_best_score_for_settings_returns_zero_when_empty() -> None:
    data = PersistentData(settings=UserSettings(), leaderboard={})
    assert best_score_for_settings(data, data.settings) == 0


def test_best_score_for_settings_returns_top_score() -> None:
    settings = UserSettings(difficulty=Difficulty.HARD, map_mode=MapMode.WRAP, obstacles_enabled=True)
    key = leaderboard_key(settings)
    data = PersistentData(settings=UserSettings(), leaderboard={key: [25, 19, 4]})
    assert best_score_for_settings(data, settings) == 25


def test_update_run_stats_tracks_totals() -> None:
    data = PersistentData()
    update_run_stats(data, 12)
    update_run_stats(data, 5)

    assert data.stats.total_runs == 2
    assert data.stats.total_score == 17
    assert data.stats.best_score_global == 12


def test_load_migrates_v2_schema_payload(tmp_path: Path) -> None:
    path = tmp_path / "save.json"
    v2_payload = {
        "settings": {
            "difficulty": "normal",
            "map_mode": "bounded",
            "obstacles_enabled": False,
            "muted": False,
        },
        "leaderboard": {"normal|bounded|clear": [17, 11]},
    }
    path.write_text(json.dumps(v2_payload), encoding="utf-8")

    loaded = load_persistent_data(path)

    assert loaded.schema_version == SAVE_SCHEMA_VERSION
    assert loaded.stats.best_score_global == 17
    assert loaded.achievements == []
    assert loaded.graphics.theme_id == ThemeId.NEON
    assert loaded.onboarding_seen is False


def test_load_migrates_v3_schema_payload_with_default_graphics(tmp_path: Path) -> None:
    path = tmp_path / "save.json"
    v3_payload = {
        "schema_version": 3,
        "settings": {
            "difficulty": "hard",
            "map_mode": "wrap",
            "obstacles_enabled": True,
            "muted": False,
        },
        "leaderboard": {"hard|wrap|obs": [21, 12]},
        "stats": {"total_runs": 3, "total_score": 40, "best_score_global": 21},
        "achievements": ["first_run"],
    }
    path.write_text(json.dumps(v3_payload), encoding="utf-8")

    loaded = load_persistent_data(path)

    assert loaded.schema_version == SAVE_SCHEMA_VERSION
    assert loaded.graphics.theme_id == ThemeId.NEON
    assert loaded.graphics.show_grid is True
    assert loaded.onboarding_seen is False


def test_invalid_graphics_values_fall_back_to_defaults(tmp_path: Path) -> None:
    path = tmp_path / "save.json"
    payload = {
        "schema_version": SAVE_SCHEMA_VERSION,
        "settings": {"difficulty": "normal", "map_mode": "bounded", "obstacles_enabled": False, "muted": False},
        "graphics": {"theme_id": "invalid-theme", "ui_scale": 0, "show_grid": "no"},
        "leaderboard": {},
        "stats": {"total_runs": 0, "total_score": 0, "best_score_global": 0},
        "achievements": [],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")

    loaded = load_persistent_data(path)

    assert loaded.graphics.theme_id == ThemeId.NEON
    assert loaded.graphics.ui_scale == 1.0
    assert loaded.graphics.show_grid is False


def test_onboarding_flag_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "save.json"
    data = PersistentData(onboarding_seen=True)
    save_persistent_data(data, path)
    loaded = load_persistent_data(path)
    assert loaded.onboarding_seen is True
