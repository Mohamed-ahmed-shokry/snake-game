from snake_game.persistence import PersistentData, update_run_stats
from snake_game.systems.achievements import (
    ACHIEVEMENTS,
    achievement_label,
    unlock_run_achievements,
)


def test_first_completed_run_unlocks_first_run() -> None:
    data = PersistentData()
    update_run_stats(data, 4)

    unlocked = unlock_run_achievements(
        data,
        score=4,
        stage_reached=1,
        food_eaten=2,
        run_seconds=12.0,
    )

    assert unlocked == ["first_run"]
    assert data.achievements == ["first_run"]


def test_run_unlocks_each_met_milestone_in_display_order() -> None:
    data = PersistentData()
    update_run_stats(data, 30)

    unlocked = unlock_run_achievements(
        data,
        score=30,
        stage_reached=3,
        food_eaten=10,
        run_seconds=60.0,
    )

    assert unlocked == [achievement.id for achievement in ACHIEVEMENTS]


def test_existing_achievements_are_not_unlocked_twice() -> None:
    data = PersistentData(achievements=["first_run", "score_25"])
    update_run_stats(data, 30)

    unlocked = unlock_run_achievements(
        data,
        score=30,
        stage_reached=1,
        food_eaten=1,
        run_seconds=10.0,
    )

    assert unlocked == []
    assert data.achievements == ["first_run", "score_25"]


def test_unknown_achievement_label_has_readable_fallback() -> None:
    assert achievement_label("secret_move") == "Secret Move"
