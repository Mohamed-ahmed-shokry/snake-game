from __future__ import annotations

from dataclasses import dataclass

from snake_game.persistence import PersistentData


@dataclass(frozen=True, slots=True)
class Achievement:
    id: str
    label: str
    description: str


ACHIEVEMENTS: tuple[Achievement, ...] = (
    Achievement("first_run", "First Run", "Complete your first run."),
    Achievement("score_25", "Quarter Century", "Score at least 25 points in one run."),
    Achievement("stage_3", "Stage Climber", "Reach stage 3."),
    Achievement("food_10", "Big Appetite", "Eat at least 10 food in one run."),
    Achievement("survivor_60", "Survivor", "Stay alive for at least 60 seconds."),
)

_ACHIEVEMENTS_BY_ID = {achievement.id: achievement for achievement in ACHIEVEMENTS}


def achievement_label(achievement_id: str) -> str:
    achievement = _ACHIEVEMENTS_BY_ID.get(achievement_id)
    return (
        achievement.label if achievement is not None else achievement_id.replace("_", " ").title()
    )


def unlock_run_achievements(
    data: PersistentData,
    *,
    score: int,
    stage_reached: int,
    food_eaten: int,
    run_seconds: float,
) -> list[str]:
    earned = {
        "first_run": data.stats.total_runs >= 1,
        "score_25": score >= 25,
        "stage_3": stage_reached >= 3,
        "food_10": food_eaten >= 10,
        "survivor_60": run_seconds >= 60.0,
    }
    existing = set(data.achievements)
    unlocked: list[str] = []
    for achievement in ACHIEVEMENTS:
        if earned[achievement.id] and achievement.id not in existing:
            data.achievements.append(achievement.id)
            existing.add(achievement.id)
            unlocked.append(achievement.id)
    return unlocked
