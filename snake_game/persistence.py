from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from snake_game.config import UserSettings
from snake_game.types import Difficulty, MapMode


@dataclass(slots=True)
class PersistentData:
    settings: UserSettings
    leaderboard: dict[str, list[int]]


def leaderboard_key(settings: UserSettings) -> str:
    obstacle_tag = "obs" if settings.obstacles_enabled else "clear"
    return f"{settings.difficulty.value}|{settings.map_mode.value}|{obstacle_tag}"


def _settings_to_dict(settings: UserSettings) -> dict[str, object]:
    return {
        "difficulty": settings.difficulty.value,
        "map_mode": settings.map_mode.value,
        "obstacles_enabled": settings.obstacles_enabled,
        "muted": settings.muted,
    }


def _settings_from_dict(data: object) -> UserSettings:
    if not isinstance(data, dict):
        return UserSettings()

    difficulty_value = str(data.get("difficulty", Difficulty.NORMAL.value))
    map_mode_value = str(data.get("map_mode", MapMode.BOUNDED.value))

    try:
        difficulty = Difficulty(difficulty_value)
    except ValueError:
        difficulty = Difficulty.NORMAL

    try:
        map_mode = MapMode(map_mode_value)
    except ValueError:
        map_mode = MapMode.BOUNDED

    return UserSettings(
        difficulty=difficulty,
        map_mode=map_mode,
        obstacles_enabled=bool(data.get("obstacles_enabled", False)),
        muted=bool(data.get("muted", False)),
    )


def _normalize_leaderboard(data: object) -> dict[str, list[int]]:
    if not isinstance(data, dict):
        return {}

    normalized: dict[str, list[int]] = {}
    for key, values in data.items():
        if not isinstance(key, str):
            continue
        if not isinstance(values, list):
            continue
        clean_values = [int(value) for value in values if isinstance(value, (int, float))]
        clean_values.sort(reverse=True)
        normalized[key] = clean_values[:10]
    return normalized


def _backup_corrupt_file(path: Path) -> None:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = path.with_suffix(f"{path.suffix}.corrupt-{timestamp}")
    try:
        path.replace(backup_path)
    except OSError:
        pass


def load_persistent_data(path: Path) -> PersistentData:
    if not path.exists():
        return PersistentData(settings=UserSettings(), leaderboard={})

    try:
        content = path.read_text(encoding="utf-8")
        payload = json.loads(content)
    except (OSError, json.JSONDecodeError):
        _backup_corrupt_file(path)
        return PersistentData(settings=UserSettings(), leaderboard={})

    if not isinstance(payload, dict):
        _backup_corrupt_file(path)
        return PersistentData(settings=UserSettings(), leaderboard={})

    settings = _settings_from_dict(payload.get("settings"))
    leaderboard = _normalize_leaderboard(payload.get("leaderboard"))
    return PersistentData(settings=settings, leaderboard=leaderboard)


def save_persistent_data(data: PersistentData, path: Path) -> None:
    payload = {
        "settings": _settings_to_dict(data.settings),
        "leaderboard": data.leaderboard,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def record_score(data: PersistentData, settings: UserSettings, score: int, limit: int) -> list[int]:
    key = leaderboard_key(settings)
    table = list(data.leaderboard.get(key, []))
    table.append(max(score, 0))
    table.sort(reverse=True)
    trimmed = table[:limit]
    data.leaderboard[key] = trimmed
    return trimmed

