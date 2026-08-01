import math

import pytest

from snake_game.config import GameConfig, GraphicsSettings


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("window_width", 800.0),
        ("window_height", math.inf),
        ("cell_size", True),
        ("render_fps", math.nan),
        ("max_steps_per_frame", 1.5),
        ("obstacle_count", math.nan),
        ("leaderboard_limit", 1.5),
        ("stage_points_interval", math.inf),
    ],
)
def test_validate_rejects_non_integer_runtime_fields(field_name: str, value: object) -> None:
    config = GameConfig()
    setattr(config, field_name, value)

    with pytest.raises(ValueError, match=f"{field_name} must be an integer"):
        config.validate()


@pytest.mark.parametrize("value", [math.nan, math.inf, "3"])
def test_validate_rejects_invalid_countdown_values(value: object) -> None:
    config = GameConfig(countdown_seconds=value)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="countdown_seconds must be finite"):
        config.validate()


@pytest.mark.parametrize("value", [math.nan, math.inf, "1.0"])
def test_validate_rejects_invalid_ui_scale_values(value: object) -> None:
    config = GameConfig(graphics=GraphicsSettings(ui_scale=value))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="graphics.ui_scale must be finite"):
        config.validate()


def test_validate_rejects_invalid_graphics_object() -> None:
    config = GameConfig(graphics=None)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="graphics must be a GraphicsSettings"):
        config.validate()


def test_validate_rejects_invalid_data_file_type() -> None:
    config = GameConfig(data_file=None)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="data_file must not be empty"):
        config.validate()
