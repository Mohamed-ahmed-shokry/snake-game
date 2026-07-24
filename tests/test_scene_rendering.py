from __future__ import annotations

import random
from pathlib import Path

import pygame
import pytest

from snake_game.config import GameConfig
from snake_game.events import EventBus
from snake_game.persistence import PersistentData
from snake_game.scenes.base import AppContext, SessionResult
from snake_game.scenes.game_over_scene import GameOverScene
from snake_game.scenes.menu_scene import MenuScene
from snake_game.scenes.play_scene import PlayScene
from snake_game.scenes.progress_scene import ProgressScene
from snake_game.scenes.settings_scene import SettingsScene


class SilentAudio:
    def play(self, event_name: str) -> None:
        _ = event_name

    def set_muted(self, muted: bool) -> None:
        _ = muted


@pytest.fixture
def app_context(tmp_path: Path) -> AppContext:
    pygame.font.init()
    config = GameConfig()
    persistent_data = PersistentData()
    config.graphics = persistent_data.graphics
    return AppContext(
        config=config,
        data_path=tmp_path / "save.json",
        persistent_data=persistent_data,
        audio=SilentAudio(),  # type: ignore[arg-type]
        event_bus=EventBus(),
        rng=random.Random(7),
        title_font=pygame.font.Font(None, 76),
        body_font=pygame.font.Font(None, 42),
        small_font=pygame.font.Font(None, 28),
    )


def test_every_scene_renders_at_default_viewport(app_context: AppContext) -> None:
    app_context.last_result = SessionResult(
        score=30,
        leaderboard_key="normal|bounded|clear",
        leaderboard=[30, 20, 10],
        is_new_high_score=True,
        stage_reached=3,
        food_eaten=10,
        run_seconds=65.0,
        new_achievements=["first_run", "score_25"],
    )
    screen = pygame.Surface((app_context.config.window_width, app_context.config.window_height))
    scenes = [
        MenuScene(app_context),
        ProgressScene(app_context),
        SettingsScene(app_context),
        PlayScene(app_context),
        GameOverScene(app_context),
    ]

    for scene in scenes:
        screen.fill((0, 0, 0))
        scene.render(screen)
        assert screen.get_at((0, 0))[:3] != (0, 0, 0)
