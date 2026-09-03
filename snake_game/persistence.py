from __future__ import annotations

import json
import math
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

from snake_game.config import GraphicsSettings, KeyBindings, UserSettings, normalize_colorblind_mode
from snake_game.types import Difficulty, MapMode, ThemeId

SAVE_SCHEMA_VERSION = 4
MAX_SAVE_FILE_BYTES = 1024 * 1024


@dataclass(slots=True)
class PlayerStats:
    total_runs: int = 0
    total_score: int = 0
    best_score_global: int = 0


@dataclass(slots=True)
class PersistentData:
    settings: UserSettings = field(default_factory=UserSettings)
    graphics: GraphicsSettings = field(default_factory=GraphicsSettings)
    leaderboard: dict[str, list[int]] = field(default_factory=dict)
    stats: PlayerStats = field(default_factory=PlayerStats)
    achievements: list[str] = field(default_factory=list)
    onboarding_seen: bool = False
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
        "key_bindings": settings.key_bindings.to_dict(),
    }


def _graphics_to_dict(graphics: GraphicsSettings) -> dict[str, object]:
    return {
        "theme_id": graphics.theme_id.value,
        "ui_scale": graphics.ui_scale,
        "show_grid": graphics.show_grid,
        "particles_enabled": graphics.particles_enabled,
        "screen_shake_enabled": graphics.screen_shake_enabled,
        "reduced_motion": graphics.reduced_motion,
        "colorblind_mode": graphics.colorblind_mode,
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
        obstacles_enabled=_coerce_bool(data.get("obstacles_enabled"), False),
        muted=_coerce_bool(data.get("muted"), False),
        key_bindings=KeyBindings.from_dict(data.get("key_bindings")),
    )


def _coerce_bool(value: object, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
    return default


def _coerce_positive_float(value: object, default: float) -> float:
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        try:
            parsed = float(value)
        except OverflowError:
            return default
        return parsed if math.isfinite(parsed) and parsed > 0 else default
    if isinstance(value, str):
        try:
            parsed = float(value)
        except ValueError:
            return default
        return parsed if math.isfinite(parsed) and parsed > 0 else default
    return default


def _graphics_from_dict(data: object) -> GraphicsSettings:
    if not isinstance(data, dict):
        return GraphicsSettings()

    raw_theme_id = str(data.get("theme_id", ThemeId.NEON.value))
    try:
        theme_id = ThemeId(raw_theme_id)
    except ValueError:
        theme_id = ThemeId.NEON

    return GraphicsSettings(
        theme_id=theme_id,
        ui_scale=_coerce_positive_float(data.get("ui_scale"), 1.0),
        show_grid=_coerce_bool(data.get("show_grid"), True),
        particles_enabled=_coerce_bool(data.get("particles_enabled"), True),
        screen_shake_enabled=_coerce_bool(data.get("screen_shake_enabled"), False),
        reduced_motion=_coerce_bool(data.get("reduced_motion"), False),
        colorblind_mode=normalize_colorblind_mode(data.get("colorblind_mode")),
    )


def _coerce_non_negative_int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return max(0, value)
    if isinstance(value, float):
        if not math.isfinite(value):
            return 0
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
        clean_values: list[int] = []
        for value in values:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                continue
            if isinstance(value, float) and not math.isfinite(value):
                continue
            if value < 0:
                continue
            clean_values.append(int(value))
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


def _backup_file(path: Path, reason: str) -> None:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    backup_path = path.with_suffix(f"{path.suffix}.{reason}-{timestamp}")
    with suppress(OSError):
        path.replace(backup_path)


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
    if version < 4:
        migrated.setdefault("graphics", _graphics_to_dict(GraphicsSettings()))
    migrated.setdefault("onboarding_seen", False)

    migrated["schema_version"] = SAVE_SCHEMA_VERSION
    return migrated


def load_persistent_data(path: Path) -> PersistentData:
    if not path.exists():
        return PersistentData()
    if not path.is_file():
        return PersistentData()

    try:
        if path.stat().st_size > MAX_SAVE_FILE_BYTES:
            _backup_file(path, "corrupt")
            return PersistentData()
        content = path.read_text(encoding="utf-8")
        payload = json.loads(content)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, RecursionError):
        _backup_file(path, "corrupt")
        return PersistentData()

    if not isinstance(payload, dict):
        _backup_file(path, "corrupt")
        return PersistentData()

    schema_version = payload.get("schema_version")
    if (
        isinstance(schema_version, int)
        and not isinstance(schema_version, bool)
        and schema_version > SAVE_SCHEMA_VERSION
    ):
        _backup_file(path, "unsupported")
        return PersistentData()

    migrated = _migrate_payload(payload)
    leaderboard = _normalize_leaderboard(migrated.get("leaderboard"))
    settings = _settings_from_dict(migrated.get("settings"))
    graphics = _graphics_from_dict(migrated.get("graphics"))
    stats = _stats_from_dict(migrated.get("stats"))
    achievements = _normalize_achievements(migrated.get("achievements"))
    onboarding_seen = _coerce_bool(migrated.get("onboarding_seen"), False)
    return PersistentData(
        settings=settings,
        graphics=graphics,
        leaderboard=leaderboard,
        stats=stats,
        achievements=achievements,
        onboarding_seen=onboarding_seen,
        schema_version=SAVE_SCHEMA_VERSION,
    )


def save_persistent_data(data: PersistentData, path: Path) -> None:
    payload = {
        "schema_version": SAVE_SCHEMA_VERSION,
        "settings": _settings_to_dict(data.settings),
        "graphics": _graphics_to_dict(data.graphics),
        "leaderboard": data.leaderboard,
        "stats": _stats_to_dict(data.stats),
        "achievements": data.achievements,
        "onboarding_seen": data.onboarding_seen,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            json.dump(payload, temporary_file, indent=2, allow_nan=False)
            temporary_file.write("\n")
        temporary_path.replace(path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            with suppress(OSError):
                temporary_path.unlink()


def record_score(data: PersistentData, settings: UserSettings, score: int, limit: int) -> list[int]:
    key = leaderboard_key(settings)
    table = [value for value in data.leaderboard.get(key, []) if value > 0]
    if score > 0:
        table.append(score)
    table.sort(reverse=True)
    trimmed = table[:limit]
    data.leaderboard[key] = trimmed
    return trimmed
