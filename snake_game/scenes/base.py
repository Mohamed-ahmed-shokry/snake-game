from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path

import pygame

from snake_game.audio import AudioManager
from snake_game.config import GameConfig
from snake_game.events import EventBus
from snake_game.persistence import PersistentData
from snake_game.types import SceneId


@dataclass(slots=True)
class SessionResult:
    score: int
    leaderboard_key: str
    leaderboard: list[int]
    is_new_high_score: bool


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
