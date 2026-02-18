from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from snake_game.config import UserSettings
from snake_game.types import Difficulty, MapMode

SAVE_SCHEMA_VERSION = 3


@dataclass(slots=True)
class PlayerStats:
    total_runs: int = 0
    total_score: int = 0
    best_score_global: int = 0


@dataclass(slots=True)
class PersistentData:
    settings: UserSettings = field(default_factory=UserSettings)
    leaderboard: dict[str, list[int]] = field(default_factory=dict)
    stats: PlayerStats = field(default_factory=PlayerStats)
    achievements: list[str] = field(default_factory=list)
    schema_version: int = SAVE_SCHEMA_VERSION


def is_new_high_score(existing_scores: list[int], candidate_score: int) -> bool:
    if candidate_score <= 0:
        return False
    if not existing_scores:
        return True
    return candidate_score > max(existing_scores)


def best_score_for_settings(data: PersistentData, settings: UserSettings) -> int:
    key = leaderboard_key(settings)
    scores = data.leaderboard.get(key, [])
    return scores[0] if scores else 0


def leaderboard_key(settings: UserSettings) -> str:
    obstacle_tag = "obs" if settings.obstacles_enabled else "clear"
    return f"{settings.difficulty.value}|{settings.map_mode.value}|{obstacle_tag}"


def update_run_stats(data: PersistentData, score: int) -> None:
    safe_score = max(score, 0)
    data.stats.total_runs += 1
    data.stats.total_score += safe_score
    data.stats.best_score_global = max(data.stats.best_score_global, safe_score)


def _settings_to_dict(settings: UserSettings) -> dict[str, object]:
    return {
        "difficulty": settings.difficulty.value,
        "map_mode": settings.map_mode.value,
        "obstacles_enabled": settings.obstacles_enabled,
        "muted": settings.muted,
    }


def _stats_to_dict(stats: PlayerStats) -> dict[str, int]:
    return {
        "total_runs": stats.total_runs,
        "total_score": stats.total_score,
        "best_score_global": stats.best_score_global,
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


def _coerce_non_negative_int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return max(0, int(value))
    return 0


def _stats_from_dict(data: object) -> PlayerStats:
    if not isinstance(data, dict):
        return PlayerStats()
    return PlayerStats(
        total_runs=_coerce_non_negative_int(data.get("total_runs")),
        total_score=_coerce_non_negative_int(data.get("total_score")),
        best_score_global=_coerce_non_negative_int(data.get("best_score_global")),
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


def _normalize_achievements(data: object) -> list[str]:
    if not isinstance(data, list):
        return []
    names = [str(item) for item in data if isinstance(item, str)]
    seen: set[str] = set()
    unique: list[str] = []
    for name in names:
        if name in seen:
            continue
        seen.add(name)
        unique.append(name)
    return unique


def _backup_corrupt_file(path: Path) -> None:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = path.with_suffix(f"{path.suffix}.corrupt-{timestamp}")
    try:
        path.replace(backup_path)
    except OSError:
        pass


def _best_global_from_leaderboard(leaderboard: dict[str, list[int]]) -> int:
    best = 0
    for scores in leaderboard.values():
        if not scores:
            continue
        best = max(best, scores[0])
    return best


def _migrate_payload(payload: dict[str, object]) -> dict[str, object]:
    migrated = dict(payload)
    version = payload.get("schema_version")
    if not isinstance(version, int):
        version = 2

    if version < 3:
        leaderboard = _normalize_leaderboard(payload.get("leaderboard"))
        migrated.setdefault(
            "stats",
            {
                "total_runs": 0,
                "total_score": 0,
                "best_score_global": _best_global_from_leaderboard(leaderboard),
            },
        )
        migrated.setdefault("achievements", [])

    migrated["schema_version"] = SAVE_SCHEMA_VERSION
    return migrated


def load_persistent_data(path: Path) -> PersistentData:
    if not path.exists():
        return PersistentData()

    try:
        content = path.read_text(encoding="utf-8")
        payload = json.loads(content)
    except (OSError, json.JSONDecodeError):
        _backup_corrupt_file(path)
        return PersistentData()

    if not isinstance(payload, dict):
        _backup_corrupt_file(path)
        return PersistentData()

    migrated = _migrate_payload(payload)
    leaderboard = _normalize_leaderboard(migrated.get("leaderboard"))
    settings = _settings_from_dict(migrated.get("settings"))
    stats = _stats_from_dict(migrated.get("stats"))
    achievements = _normalize_achievements(migrated.get("achievements"))
    return PersistentData(
        settings=settings,
        leaderboard=leaderboard,
        stats=stats,
        achievements=achievements,
        schema_version=SAVE_SCHEMA_VERSION,
    )


def save_persistent_data(data: PersistentData, path: Path) -> None:
    payload = {
        "schema_version": SAVE_SCHEMA_VERSION,
        "settings": _settings_to_dict(data.settings),
        "leaderboard": data.leaderboard,
        "stats": _stats_to_dict(data.stats),
        "achievements": data.achievements,
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

