from pathlib import Path

import pygame
import pytest

import snake_game.app as app
from snake_game.config import GameConfig, GamepadSettings


def test_run_quits_pygame_when_configuration_is_invalid(tmp_path: Path) -> None:
    pygame.quit()
    config = GameConfig(window_width=0, data_file=str(tmp_path / "save.json"))

    with pytest.raises(ValueError):
        app.run(config)

    assert pygame.get_init() is False


def test_run_logs_final_save_failure_and_quits_cleanly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    pygame.quit()
    config = GameConfig(data_file=str(tmp_path / "save.json"))
    monkeypatch.setattr(
        app,
        "_create_display",
        lambda _config, fullscreen=False: pygame.Surface(
            (_config.window_width, _config.window_height)
        ),
    )
    monkeypatch.setattr(
        pygame.event,
        "get",
        lambda: [pygame.event.Event(pygame.QUIT)],
    )

    def fail_save(*_args: object, **_kwargs: object) -> None:
        raise OSError("disk unavailable")

    monkeypatch.setattr("snake_game.scenes.base.save_persistent_data", fail_save)

    with caplog.at_level("WARNING"):
        app.run(config)

    assert pygame.get_init() is False
    assert "disk unavailable" in caplog.text


def test_init_gamepad_returns_empty_when_no_joystick(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pygame.joystick, "get_count", lambda: 0)
    monkeypatch.setattr(pygame.joystick, "init", lambda: None)

    gamepads = app._init_gamepad()
    assert gamepads == []


def test_handle_gamepad_button_down_mute(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pygame.quit()
    pygame.init()
    config = GameConfig(data_file=str(tmp_path / "save.json"))
    monkeypatch.setattr(
        app,
        "_create_display",
        lambda _config, fullscreen=False: pygame.Surface(
            (_config.window_width, _config.window_height)
        ),
    )
    monkeypatch.setattr(
        pygame.event,
        "get",
        lambda: [pygame.event.Event(pygame.QUIT)],
    )

    # Create a mock context
    import random

    from snake_game.audio import AudioManager
    from snake_game.config import UserSettings
    from snake_game.events import EventBus
    from snake_game.persistence import PersistentData
    from snake_game.scenes.base import AppContext, build_ui_fonts

    config = GameConfig(data_file=str(tmp_path / "save.json"))
    config.validate()
    persistent_data = PersistentData(
        settings=UserSettings(gamepad_settings=GamepadSettings(enabled=True, button_mute=5))
    )
    title_font, body_font, small_font = build_ui_fonts(config)
    audio = AudioManager(muted=False)
    ctx = AppContext(
        config=config,
        data_path=tmp_path / "save.json",
        persistent_data=persistent_data,
        audio=audio,
        event_bus=EventBus(),
        rng=random.Random(42),
        title_font=title_font,
        body_font=body_font,
        small_font=small_font,
    )

    # Test mute button
    event = pygame.event.Event(pygame.JOYBUTTONDOWN, button=5)
    result = app._handle_gamepad_button_down(ctx, event.button)
    assert result is True
    assert persistent_data.settings.muted is True
    assert audio.muted is True

    # Test non-mute button
    event = pygame.event.Event(pygame.JOYBUTTONDOWN, button=0)
    result = app._handle_gamepad_button_down(ctx, event.button)
    assert result is False


def test_get_gamepad_direction_returns_none_when_no_joystick(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pygame.quit()
    pygame.init()
    monkeypatch.setattr(pygame.joystick, "get_count", lambda: 0)

    import random

    from snake_game.audio import AudioManager
    from snake_game.config import GameConfig, UserSettings
    from snake_game.events import EventBus
    from snake_game.persistence import PersistentData
    from snake_game.scenes.base import AppContext, build_ui_fonts

    config = GameConfig()
    config.validate()
    persistent_data = PersistentData(
        settings=UserSettings(gamepad_settings=GamepadSettings(enabled=True))
    )
    title_font, body_font, small_font = build_ui_fonts(config)
    audio = AudioManager(muted=False)
    ctx = AppContext(
        config=config,
        data_path=Path("save.json"),
        persistent_data=persistent_data,
        audio=audio,
        event_bus=EventBus(),
        rng=random.Random(42),
        title_font=title_font,
        body_font=body_font,
        small_font=small_font,
    )

    result = app._get_gamepad_direction(ctx)
    assert result is None
