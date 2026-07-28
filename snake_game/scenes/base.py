from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from pathlib import Path

import pygame

from snake_game.audio import AudioManager
from snake_game.config import GameConfig
from snake_game.events import EventBus
from snake_game.persistence import PersistentData, save_persistent_data
from snake_game.types import SceneId

UI_SCALE_OPTIONS: tuple[float, ...] = (0.85, 1.0, 1.1)
logger = logging.getLogger(__name__)


def build_ui_fonts(
    config: GameConfig,
) -> tuple[pygame.font.Font, pygame.font.Font, pygame.font.Font]:
    scale = min(max(config.graphics.ui_scale, UI_SCALE_OPTIONS[0]), UI_SCALE_OPTIONS[-1])
    return (
        pygame.font.Font(None, round(76 * scale)),
        pygame.font.Font(None, round(42 * scale)),
        pygame.font.Font(None, round(28 * scale)),
    )


@dataclass(slots=True)
class SessionResult:
    score: int
    leaderboard_key: str
    leaderboard: list[int]
    is_new_high_score: bool
    stage_reached: int = 1
    food_eaten: int = 0
    run_seconds: float = 0.0
    new_achievements: list[str] = field(default_factory=list)
    end_reason: str = "collision"


@dataclass(slots=True)
class AppContext:
    config: GameConfig
    data_path: Path
    persistent_data: PersistentData
    audio: AudioManager
    event_bus: EventBus
    rng: random.Random
    title_font: pygame.font.Font
    body_font: pygame.font.Font
    small_font: pygame.font.Font
    last_result: SessionResult | None = None
    save_error_message: str | None = None

    def refresh_fonts(self) -> None:
        self.title_font, self.body_font, self.small_font = build_ui_fonts(self.config)

    def persist(self) -> bool:
        try:
            save_persistent_data(self.persistent_data, self.data_path)
        except (OSError, ValueError) as error:
            self.save_error_message = "Save failed - progress may be lost"
            logger.warning("Could not save game data to %s: %s", self.data_path, error)
            return False
        self.save_error_message = None
        return True


class Scene:
    scene_id: SceneId

    def __init__(self, ctx: AppContext) -> None:
        self.ctx = ctx
        self.next_scene: SceneId | None = None
        self.quit_requested = False

    def handle_event(self, event: pygame.event.Event) -> None:
        raise NotImplementedError

    def update(self, delta_seconds: float) -> None:
        raise NotImplementedError

    def render(self, screen: pygame.Surface) -> None:
        raise NotImplementedError

    def consume_next_scene(self) -> SceneId | None:
        next_scene = self.next_scene
        self.next_scene = None
        return next_scene
