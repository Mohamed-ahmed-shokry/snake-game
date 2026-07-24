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
from snake_game.systems.powerups import PowerUpType
from snake_game.ui.theme import resolve_theme
from snake_game.rendering.assets import RenderAssets
from snake_game.rendering.layers import PlayfieldRenderer


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


def test_powerup_types_have_distinct_visual_glyphs(app_context: AppContext) -> None:
    play_scene = PlayScene(app_context)
    renderer = PlayfieldRenderer(
        config=app_context.config,
        theme=resolve_theme(app_context.config.graphics.theme_id),
        assets=RenderAssets(),
    )
    images: list[bytes] = []

    for powerup_type in PowerUpType:
        screen = pygame.Surface((app_context.config.window_width, app_context.config.window_height))
        renderer.render(
            screen=screen,
            state=play_scene.state,
            hud_font=app_context.title_font,
            small_font=app_context.small_font,
            countdown_remaining=0.0,
            best_score=0,
            stage=1,
            powerup_position=(1, 1),
            powerup_type=powerup_type,
            active_effect_labels=[],
        )
        images.append(pygame.image.tobytes(screen.subsurface(pygame.Rect(20, 20, 20, 20)), "RGB"))

    assert len(set(images)) == len(PowerUpType)
