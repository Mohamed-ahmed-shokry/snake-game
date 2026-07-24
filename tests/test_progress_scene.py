from snake_game.config import UserSettings
from snake_game.persistence import PersistentData, PlayerStats, leaderboard_key
from snake_game.scenes.progress_scene import progress_summary_lines


def test_progress_summary_uses_saved_stats_and_current_setup_best() -> None:
    settings = UserSettings()
    data = PersistentData(
        settings=settings,
        leaderboard={leaderboard_key(settings): [14, 9]},
        stats=PlayerStats(total_runs=3, total_score=27, best_score_global=14),
    )

    assert progress_summary_lines(data) == [
        "Runs Completed: 3",
        "Total Score: 27",
        "Global Best: 14",
        "Current Setup Best: 14",
    ]
