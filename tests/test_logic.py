import random

from snake_game.config import GameConfig
from snake_game.logic import (
    advance_one_step,
    advance_simulation,
    create_initial_state,
    queue_direction_change,
    spawn_food,
)
from snake_game.types import Direction, GameStatus


def make_config() -> GameConfig:
    config = GameConfig(
        window_width=200,
        window_height=200,
        cell_size=20,
        base_steps_per_second=5.0,
        speed_increment_per_food=0.5,
        max_steps_per_second=6.0,
        max_steps_per_frame=3,
    )
    config.validate()
    return config


def test_create_initial_state_has_valid_shape() -> None:
    config = make_config()
    state = create_initial_state(config, random.Random(1))

    assert len(state.snake) == 3
    assert state.direction == Direction.RIGHT
    assert state.pending_direction is None
    assert state.status == GameStatus.RUNNING
    assert state.food not in state.snake


def test_queue_direction_change_blocks_reverse_direction() -> None:
    config = make_config()
    state = create_initial_state(config, random.Random(2))

    queue_direction_change(state, Direction.LEFT)
    assert state.pending_direction is None

    queue_direction_change(state, Direction.UP)
    assert state.pending_direction == Direction.UP


def test_advance_one_step_moves_snake_and_trims_tail() -> None:
    config = make_config()
    state = create_initial_state(config, random.Random(3))
    old_snake = list(state.snake)
    state.food = (0, 0)

    advance_one_step(state, config, random.Random(3))

    assert state.snake[0] == (old_snake[0][0] + 1, old_snake[0][1])
    assert len(state.snake) == len(old_snake)
    assert state.status == GameStatus.RUNNING


def test_advance_one_step_grows_snake_and_increments_score() -> None:
    config = make_config()
    rng = random.Random(4)
    state = create_initial_state(config, rng)
    head_x, head_y = state.snake[0]
    state.food = (head_x + 1, head_y)
    old_length = len(state.snake)

    advance_one_step(state, config, rng)

    assert len(state.snake) == old_length + 1
    assert state.score == 1
    assert state.steps_per_second > config.base_steps_per_second
    assert state.status == GameStatus.RUNNING


def test_wall_collision_sets_game_over() -> None:
    config = make_config()
    state = create_initial_state(config, random.Random(5))
    state.snake = [(config.grid_width - 1, 2), (config.grid_width - 2, 2), (config.grid_width - 3, 2)]
    state.direction = Direction.RIGHT
    state.food = (0, 0)

    advance_one_step(state, config, random.Random(5))

    assert state.status == GameStatus.GAME_OVER


def test_self_collision_sets_game_over() -> None:
    config = make_config()
    state = create_initial_state(config, random.Random(6))
    state.snake = [(5, 5), (4, 5), (4, 4), (5, 4), (6, 4), (6, 5)]
    state.direction = Direction.LEFT
    state.food = (0, 0)

    advance_one_step(state, config, random.Random(6))

    assert state.status == GameStatus.GAME_OVER


def test_speed_increase_is_capped() -> None:
    config = make_config()
    rng = random.Random(7)
    state = create_initial_state(config, rng)
    state.steps_per_second = config.max_steps_per_second - 0.1
    head_x, head_y = state.snake[0]
    state.food = (head_x + 1, head_y)

    advance_one_step(state, config, rng)

    assert state.steps_per_second == config.max_steps_per_second


def test_spawn_food_never_overlaps_snake() -> None:
    rng = random.Random(8)
    snake = [(0, 0), (1, 0), (2, 0), (3, 0)]

    food = spawn_food(snake, grid_width=4, grid_height=2, rng=rng)

    assert food not in snake


def test_advance_simulation_uses_accumulated_delta() -> None:
    config = make_config()
    state = create_initial_state(config, random.Random(9))
    state.food = (0, 0)

    steps = advance_simulation(state, config, delta_seconds=0.45, rng=random.Random(9))

    assert steps == 2
    assert state.snake[0] == (7, 5)
    assert 0.0 < state.accumulator_seconds < 0.2


def test_advance_simulation_caps_steps_per_frame() -> None:
    config = make_config()
    state = create_initial_state(config, random.Random(10))
    state.food = (0, 0)

    steps = advance_simulation(state, config, delta_seconds=2.0, rng=random.Random(10))

    assert steps == config.max_steps_per_frame

