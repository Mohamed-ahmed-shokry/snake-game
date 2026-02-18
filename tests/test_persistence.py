from pathlib import Path

from snake_game.config import UserSettings
from snake_game.persistence import (
    best_score_for_settings,
    PersistentData,
    is_new_high_score,
    leaderboard_key,
    load_persistent_data,
    record_score,
    save_persistent_data,
)
from snake_game.types import Difficulty, MapMode


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
        leaderboard={"easy|wrap|obs": [9, 7, 4]},
    )

    save_persistent_data(data, path)
    loaded = load_persistent_data(path)

    assert loaded.settings.difficulty == Difficulty.EASY
    assert loaded.settings.map_mode == MapMode.WRAP
    assert loaded.settings.obstacles_enabled is True
    assert loaded.settings.muted is True
    assert loaded.leaderboard["easy|wrap|obs"] == [9, 7, 4]


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
