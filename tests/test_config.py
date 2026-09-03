import math

import pytest

from snake_game.config import GameConfig, GamepadSettings, GraphicsSettings


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


def test_gamepad_settings_defaults() -> None:
    settings = GamepadSettings()
    assert settings.enabled is True
    assert settings.dead_zone == 0.3
    assert settings.button_move_up == 11
    assert settings.button_move_down == 12
    assert settings.button_move_left == 13
    assert settings.button_move_right == 14
    assert settings.button_pause == 7
    assert settings.button_mute == 6
    assert settings.button_confirm == 0
    assert settings.button_menu_back == 1
    assert settings.button_help == 3


def test_gamepad_settings_to_dict() -> None:
    settings = GamepadSettings(enabled=False, dead_zone=0.5, button_pause=8)
    data = settings.to_dict()
    assert data["enabled"] is False
    assert data["dead_zone"] == 0.5
    assert data["button_pause"] == 8
    assert data["button_confirm"] == 0  # default


def test_gamepad_settings_from_dict() -> None:
    data = {
        "enabled": False,
        "dead_zone": 0.4,
        "button_move_up": 15,
        "button_pause": 9,
    }
    settings = GamepadSettings.from_dict(data)
    assert settings.enabled is False
    assert settings.dead_zone == 0.4
    assert settings.button_move_up == 15
    assert settings.button_pause == 9
    assert settings.button_confirm == 0  # default


def test_gamepad_settings_from_dict_invalid() -> None:
    settings = GamepadSettings.from_dict("not a dict")
    assert settings.enabled is True  # default
    settings = GamepadSettings.from_dict(None)
    assert settings.enabled is True  # default


def test_gamepad_settings_coerce_values() -> None:
    data = {
        "enabled": "true",
        "dead_zone": "0.25",
        "button_move_up": "12",
    }
    settings = GamepadSettings.from_dict(data)
    assert settings.enabled is True
    assert settings.dead_zone == 0.25
    assert settings.button_move_up == 12

    data = {
        "enabled": "false",
        "dead_zone": math.nan,
        "button_move_up": math.inf,
    }
    settings = GamepadSettings.from_dict(data)
    assert settings.enabled is False
    assert settings.dead_zone == 0.3  # default
    assert settings.button_move_up == 11  # default
