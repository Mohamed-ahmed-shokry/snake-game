from snake_game.scenes.game_over_scene import (
    achievement_unlock_lines,
    end_reason_text,
    format_run_time,
    top_scores_text,
)


def test_format_run_time_uses_minutes_and_seconds() -> None:
    assert format_run_time(0) == "0:00"
    assert format_run_time(65.9) == "1:05"
    assert format_run_time(-4) == "0:00"


def test_top_scores_text_handles_empty_and_limits_scores() -> None:
    assert top_scores_text([]) == "Top Scores (Current Setup): None yet"
    assert top_scores_text([9, 7, 5, 3, 2, 1]) == "Top Scores (Current Setup): 9, 7, 5, 3, 2"


def test_achievement_unlock_lines_wrap_every_two_labels() -> None:
    assert achievement_unlock_lines(["first_run", "score_25", "stage_3"]) == [
        "Unlocked: First Run, Quarter Century",
        "Unlocked: Stage Climber",
    ]


def test_end_reason_text_explains_known_and_unknown_endings() -> None:
    assert end_reason_text("obstacle") == "Hit a stage hazard"
    assert end_reason_text("board_full") == "Board cleared - perfect run!"
    assert end_reason_text("unknown") == "Run complete"
