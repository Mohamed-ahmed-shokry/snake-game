import random

import pygame

from snake_game.config import GameConfig
from snake_game.logic import queue_direction_change, reset_state
from snake_game.state import GameState
from snake_game.types import Direction, GameStatus

KEY_TO_DIRECTION = {
    pygame.K_UP: Direction.UP,
    pygame.K_w: Direction.UP,
    pygame.K_DOWN: Direction.DOWN,
    pygame.K_s: Direction.DOWN,
    pygame.K_LEFT: Direction.LEFT,
    pygame.K_a: Direction.LEFT,
    pygame.K_RIGHT: Direction.RIGHT,
    pygame.K_d: Direction.RIGHT,
}


def handle_event(
    event: pygame.event.Event,
    state: GameState,
    config: GameConfig,
    rng: random.Random,
) -> bool:
    if event.type == pygame.QUIT:
        return False

    if event.type != pygame.KEYDOWN:
        return True

    if event.key == pygame.K_ESCAPE:
        return False

    if event.key in KEY_TO_DIRECTION:
        queue_direction_change(state, KEY_TO_DIRECTION[event.key])
        return True

    if event.key in (pygame.K_p, pygame.K_SPACE):
        if state.status == GameStatus.RUNNING:
            state.status = GameStatus.PAUSED
        elif state.status == GameStatus.PAUSED:
            state.status = GameStatus.RUNNING
        return True

    if event.key == pygame.K_r and state.status == GameStatus.GAME_OVER:
        reset_state(state, config, rng)
        return True

    return True

