import random

import pygame

from snake_game.config import GameConfig
from snake_game.input import handle_event
from snake_game.logic import advance_simulation, create_initial_state
from snake_game.render import render_frame


def main() -> None:
    pygame.init()

    config = GameConfig()
    config.validate()

    screen = pygame.display.set_mode((config.window_width, config.window_height))
    pygame.display.set_caption("Snake")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 32)

    rng = random.Random()
    state = create_initial_state(config, rng)

    running = True
    while running:
        delta_seconds = clock.tick(config.render_fps) / 1000.0

        for event in pygame.event.get():
            running = handle_event(event, state, config, rng)
            if not running:
                break

        if running:
            advance_simulation(state, config, delta_seconds, rng)
            render_frame(screen, state, config, font)
            pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
