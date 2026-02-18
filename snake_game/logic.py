import random

from snake_game.config import GameConfig
from snake_game.state import GameState
from snake_game.types import Direction, GameStatus, Point


def is_opposite(current: Direction, next_direction: Direction) -> bool:
    dx1, dy1 = current.vector
    dx2, dy2 = next_direction.vector
    return dx1 + dx2 == 0 and dy1 + dy2 == 0


def spawn_food(
    snake_cells: list[Point] | set[Point],
    grid_width: int,
    grid_height: int,
    rng: random.Random,
) -> Point:
    occupied = set(snake_cells)
    candidates = [
        (x, y)
        for y in range(grid_height)
        for x in range(grid_width)
        if (x, y) not in occupied
    ]
    if not candidates:
        raise RuntimeError("board is full, no free cell for food")
    return rng.choice(candidates)


def create_initial_state(config: GameConfig, rng: random.Random | None = None) -> GameState:
    local_rng = rng or random.Random()
    center_x = config.grid_width // 2
    center_y = config.grid_height // 2
    snake = [(center_x, center_y), (center_x - 1, center_y), (center_x - 2, center_y)]
    food = spawn_food(snake, config.grid_width, config.grid_height, local_rng)
    return GameState(
        snake=snake,
        direction=Direction.RIGHT,
        pending_direction=None,
        food=food,
        score=0,
        status=GameStatus.RUNNING,
        steps_per_second=config.base_steps_per_second,
        accumulator_seconds=0.0,
    )


def reset_state(
    state: GameState,
    config: GameConfig,
    rng: random.Random | None = None,
) -> None:
    fresh = create_initial_state(config, rng)
    state.snake = fresh.snake
    state.direction = fresh.direction
    state.pending_direction = fresh.pending_direction
    state.food = fresh.food
    state.score = fresh.score
    state.status = fresh.status
    state.steps_per_second = fresh.steps_per_second
    state.accumulator_seconds = fresh.accumulator_seconds


def queue_direction_change(state: GameState, next_direction: Direction) -> None:
    if state.status != GameStatus.RUNNING:
        return
    if is_opposite(state.direction, next_direction):
        return
    state.pending_direction = next_direction


def advance_one_step(state: GameState, config: GameConfig, rng: random.Random) -> None:
    if state.status != GameStatus.RUNNING:
        return

    if state.pending_direction is not None and not is_opposite(state.direction, state.pending_direction):
        state.direction = state.pending_direction
    state.pending_direction = None

    head_x, head_y = state.snake[0]
    move_x, move_y = state.direction.vector
    new_head = (head_x + move_x, head_y + move_y)

    new_x, new_y = new_head
    if new_x < 0 or new_x >= config.grid_width or new_y < 0 or new_y >= config.grid_height:
        state.status = GameStatus.GAME_OVER
        return

    will_grow = new_head == state.food
    body_to_check = state.snake if will_grow else state.snake[:-1]
    if new_head in body_to_check:
        state.status = GameStatus.GAME_OVER
        return

    state.snake.insert(0, new_head)

    if will_grow:
        state.score += 1
        state.steps_per_second = min(
            config.max_steps_per_second,
            state.steps_per_second + config.speed_increment_per_food,
        )
        try:
            state.food = spawn_food(state.snake, config.grid_width, config.grid_height, rng)
        except RuntimeError:
            state.status = GameStatus.GAME_OVER
    else:
        state.snake.pop()


def advance_simulation(
    state: GameState,
    config: GameConfig,
    delta_seconds: float,
    rng: random.Random,
) -> int:
    if state.status != GameStatus.RUNNING:
        return 0

    state.accumulator_seconds += max(0.0, delta_seconds)
    steps_taken = 0

    while steps_taken < config.max_steps_per_frame:
        step_interval = 1.0 / state.steps_per_second
        if state.accumulator_seconds < step_interval:
            break
        state.accumulator_seconds -= step_interval
        advance_one_step(state, config, rng)
        steps_taken += 1
        if state.status != GameStatus.RUNNING:
            break

    max_carryover = config.max_steps_per_frame * (1.0 / state.steps_per_second)
    if state.accumulator_seconds > max_carryover:
        state.accumulator_seconds = max_carryover

    return steps_taken

