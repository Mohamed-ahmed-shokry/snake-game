import random

from snake_game.config import GameConfig, UserSettings
from snake_game.logic import (
    advance_one_step,
    advance_simulation,
    create_initial_state,
    queue_direction_change,
    spawn_food,
    spawn_obstacles,
)
from snake_game.types import Difficulty, Direction, GameStatus, MapMode


def make_config() -> GameConfig:
    config = GameConfig(
        window_width=200,
        window_height=200,
        cell_size=20,
        max_steps_per_frame=3,
        obstacle_count=6,
    )
    config.validate()
    return config


def test_create_initial_state_has_valid_shape() -> None:
    config = make_config()
    settings = UserSettings()
    state = create_initial_state(config, settings, random.Random(1))

    assert len(state.snake) == 3
    assert state.direction == Direction.RIGHT
    assert state.pending_direction is None
    assert state.status == GameStatus.RUNNING
    assert state.food not in state.snake


def test_queue_direction_change_blocks_reverse_direction() -> None:
    config = make_config()
    state = create_initial_state(config, UserSettings(), random.Random(2))

    queue_direction_change(state, Direction.LEFT)
    assert state.pending_direction is None

    queue_direction_change(state, Direction.UP)
    assert state.pending_direction == Direction.UP


def test_advance_one_step_moves_snake_and_trims_tail() -> None:
    config = make_config()
    state = create_initial_state(config, UserSettings(), random.Random(3))
    old_snake = list(state.snake)
    state.food = (0, 0)

    advance_one_step(state, config, random.Random(3))

    assert state.snake[0] == (old_snake[0][0] + 1, old_snake[0][1])
    assert len(state.snake) == len(old_snake)
    assert state.status == GameStatus.RUNNING


def test_food_growth_increments_score_by_difficulty_rule() -> None:
    config = make_config()
    settings = UserSettings(difficulty=Difficulty.HARD)
    rng = random.Random(4)
    state = create_initial_state(config, settings, rng)
    head_x, head_y = state.snake[0]
    state.food = (head_x + 1, head_y)

    advance_one_step(state, config, rng)

    assert state.score == 3
    assert state.steps_per_second > 10.0


def test_food_growth_respects_score_multiplier() -> None:
    config = make_config()
    settings = UserSettings(difficulty=Difficulty.NORMAL)
    rng = random.Random(41)
    state = create_initial_state(config, settings, rng)
    head_x, head_y = state.snake[0]
    state.food = (head_x + 1, head_y)

    advance_one_step(state, config, rng, score_multiplier=2)

    assert state.score == 4


def test_wall_collision_sets_game_over_in_bounded_mode() -> None:
    config = make_config()
    settings = UserSettings(map_mode=MapMode.BOUNDED)
    state = create_initial_state(config, settings, random.Random(5))
    state.snake = [(config.grid_width - 1, 2), (config.grid_width - 2, 2), (config.grid_width - 3, 2)]
    state.direction = Direction.RIGHT
    state.food = (0, 0)

    advance_one_step(state, config, random.Random(5))

    assert state.status == GameStatus.GAME_OVER


def test_wrap_mode_wraps_head_instead_of_game_over() -> None:
    config = make_config()
    settings = UserSettings(map_mode=MapMode.WRAP)
    state = create_initial_state(config, settings, random.Random(6))
    state.snake = [(config.grid_width - 1, 2), (config.grid_width - 2, 2), (config.grid_width - 3, 2)]
    state.direction = Direction.RIGHT
    state.food = (0, 0)

    advance_one_step(state, config, random.Random(6))

    assert state.status == GameStatus.RUNNING
    assert state.snake[0] == (0, 2)


def test_obstacle_collision_sets_game_over() -> None:
    config = make_config()
    settings = UserSettings()
    state = create_initial_state(config, settings, random.Random(7))
    head_x, head_y = state.snake[0]
    state.obstacles = {(head_x + 1, head_y)}
    state.food = (0, 0)

    advance_one_step(state, config, random.Random(7))

    assert state.status == GameStatus.GAME_OVER


def test_phase_active_allows_passing_through_obstacle() -> None:
    config = make_config()
    settings = UserSettings()
    state = create_initial_state(config, settings, random.Random(71))
    head_x, head_y = state.snake[0]
    state.obstacles = {(head_x + 1, head_y)}
    state.food = (0, 0)

    advance_one_step(state, config, random.Random(71), phase_active=True)

    assert state.status == GameStatus.RUNNING
    assert state.snake[0] == (head_x + 1, head_y)


def test_phase_active_wraps_when_hitting_wall_in_bounded_mode() -> None:
    config = make_config()
    settings = UserSettings(map_mode=MapMode.BOUNDED)
    state = create_initial_state(config, settings, random.Random(72))
    state.snake = [(config.grid_width - 1, 3), (config.grid_width - 2, 3), (config.grid_width - 3, 3)]
    state.direction = Direction.RIGHT
    state.food = (0, 0)

    advance_one_step(state, config, random.Random(72), phase_active=True)

    assert state.status == GameStatus.RUNNING
    assert state.snake[0] == (0, 3)


def test_spawn_food_never_overlaps_snake_or_obstacles() -> None:
    rng = random.Random(8)
    snake = {(0, 0), (1, 0), (2, 0)}
    obstacles = {(0, 1), (1, 1)}

    food = spawn_food(snake, obstacles, grid_width=4, grid_height=2, rng=rng)

    assert food not in snake
    assert food not in obstacles


def test_spawn_obstacles_avoids_forbidden_cells() -> None:
    rng = random.Random(9)
    forbidden = {(0, 0), (1, 0), (2, 0)}
    obstacles = spawn_obstacles(4, forbidden, grid_width=5, grid_height=3, rng=rng)

    assert len(obstacles) == 4
    assert obstacles.isdisjoint(forbidden)


def test_advance_simulation_uses_accumulated_delta() -> None:
    config = make_config()
    settings = UserSettings(difficulty=Difficulty.EASY)
    state = create_initial_state(config, settings, random.Random(10))
    state.food = (0, 0)

    steps = advance_simulation(state, config, delta_seconds=0.45, rng=random.Random(10))

    assert steps == 2
    assert state.snake[0] == (7, 5)
    assert 0.0 < state.accumulator_seconds < 0.2


def test_advance_simulation_caps_steps_per_frame() -> None:
    config = make_config()
    state = create_initial_state(config, UserSettings(), random.Random(11))
    state.food = (0, 0)

    steps = advance_simulation(state, config, delta_seconds=2.0, rng=random.Random(11))

    assert steps == config.max_steps_per_frame


def test_advance_simulation_slow_time_multiplier_reduces_steps() -> None:
    config = make_config()
    settings = UserSettings(difficulty=Difficulty.NORMAL)

    fast_state = create_initial_state(config, settings, random.Random(12))
    slow_state = create_initial_state(config, settings, random.Random(12))
    fast_state.food = (0, 0)
    slow_state.food = (0, 0)

    fast_steps = advance_simulation(
        fast_state,
        config,
        delta_seconds=0.25,
        rng=random.Random(12),
        speed_multiplier=1.0,
    )
    slow_steps = advance_simulation(
        slow_state,
        config,
        delta_seconds=0.25,
        rng=random.Random(12),
        speed_multiplier=0.5,
    )

    assert slow_steps < fast_steps
