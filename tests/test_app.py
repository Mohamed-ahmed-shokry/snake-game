from pathlib import Path

import pygame
import pytest

import snake_game.app as app
from snake_game.config import GameConfig


def test_run_quits_pygame_when_configuration_is_invalid(tmp_path: Path) -> None:
    pygame.quit()
    config = GameConfig(window_width=0, data_file=str(tmp_path / "save.json"))

    with pytest.raises(ValueError):
        app.run(config)

    assert pygame.get_init() is False


def test_run_quits_pygame_when_final_save_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
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

    monkeypatch.setattr(app, "save_persistent_data", fail_save)

    with pytest.raises(OSError, match="disk unavailable"):
        app.run(config)

    assert pygame.get_init() is False
