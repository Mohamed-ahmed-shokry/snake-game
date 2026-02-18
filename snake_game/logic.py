import random

from snake_game.config import GameConfig, UserSettings, rules_for_difficulty
from snake_game.events import EventEmitter, GameEvent, GameEventType
from snake_game.state import GameState
from snake_game.types import Direction, GameStatus, MapMode, Point


def is_opposite(current: Direction, next_direction: Direction) -> bool:
    dx1, dy1 = current.vector
    dx2, dy2 = next_direction.vector
    return dx1 + dx2 == 0 and dy1 + dy2 == 0


def _emit(
    emit: EventEmitter | None,
    event_type: GameEventType,
    **payload: int | float | str | bool,
) -> None:
    if emit is None:
        return
    emit(GameEvent(type=event_type, payload=payload))


def spawn_food(
    snake_cells: list[Point] | set[Point],
    obstacle_cells: set[Point],
    grid_width: int,
    grid_height: int,
    rng: random.Random,
) -> Point:
    occupied = set(snake_cells) | obstacle_cells
    candidates = [
        (x, y)
        for y in range(grid_height)
        for x in range(grid_width)
        if (x, y) not in occupied
    ]
    if not candidates:
        raise RuntimeError("board is full, no free cell for food")
    return rng.choice(candidates)


def spawn_obstacles(
    obstacle_count: int,
    forbidden_cells: set[Point],
    grid_width: int,
    grid_height: int,
    rng: random.Random,
) -> set[Point]:
    candidates = [
        (x, y)
        for y in range(grid_height)
        for x in range(grid_width)
        if (x, y) not in forbidden_cells
    ]
    rng.shuffle(candidates)
    return set(candidates[: min(len(candidates), obstacle_count)])


def _initial_snake(config: GameConfig) -> list[Point]:
    center_x = config.grid_width // 2
    center_y = config.grid_height // 2
    return [(center_x, center_y), (center_x - 1, center_y), (center_x - 2, center_y)]


def create_initial_state(
    config: GameConfig,
    settings: UserSettings,
    rng: random.Random | None = None,
) -> GameState:
    local_rng = rng or random.Random()
    rules = rules_for_difficulty(settings.difficulty)

    snake = _initial_snake(config)
    obstacles: set[Point] = set()
    if settings.obstacles_enabled:
        center_x = config.grid_width // 2
        center_y = config.grid_height // 2
        safe_zone = {
            (center_x + dx, center_y + dy)
            for dx in range(-2, 3)
            for dy in range(-2, 3)
            if 0 <= center_x + dx < config.grid_width and 0 <= center_y + dy < config.grid_height
        }
        obstacles = spawn_obstacles(
            obstacle_count=config.obstacle_count,
            forbidden_cells=set(snake) | safe_zone,
            grid_width=config.grid_width,
            grid_height=config.grid_height,
            rng=local_rng,
        )

    food = spawn_food(snake, obstacles, config.grid_width, config.grid_height, local_rng)
    return GameState(
        snake=snake,
        direction=Direction.RIGHT,
        pending_direction=None,
        food=food,
        score=0,
        status=GameStatus.RUNNING,
        steps_per_second=rules.base_steps_per_second,
        speed_increment_per_food=rules.speed_increment_per_food,
        max_steps_per_second=rules.max_steps_per_second,
        score_per_food=rules.score_per_food,
        difficulty=settings.difficulty,
        map_mode=settings.map_mode,
        obstacles=obstacles,
        accumulator_seconds=0.0,
    )


def reset_state(
    state: GameState,
    config: GameConfig,
    settings: UserSettings,
    rng: random.Random | None = None,
) -> None:
    fresh = create_initial_state(config, settings, rng)
    state.snake = fresh.snake
    state.direction = fresh.direction
    state.pending_direction = fresh.pending_direction
    state.food = fresh.food
    state.score = fresh.score
    state.status = fresh.status
    state.steps_per_second = fresh.steps_per_second
    state.speed_increment_per_food = fresh.speed_increment_per_food
    state.max_steps_per_second = fresh.max_steps_per_second
    state.score_per_food = fresh.score_per_food
    state.difficulty = fresh.difficulty
    state.map_mode = fresh.map_mode
    state.obstacles = fresh.obstacles
    state.accumulator_seconds = fresh.accumulator_seconds


def queue_direction_change(state: GameState, next_direction: Direction) -> None:
    if state.status != GameStatus.RUNNING:
        return
    if is_opposite(state.direction, next_direction):
        return
    state.pending_direction = next_direction


def _next_head_position(state: GameState, config: GameConfig) -> Point | None:
    head_x, head_y = state.snake[0]
    move_x, move_y = state.direction.vector
    new_x, new_y = (head_x + move_x, head_y + move_y)

    if state.map_mode == MapMode.WRAP:
        return (new_x % config.grid_width, new_y % config.grid_height)

    if new_x < 0 or new_x >= config.grid_width or new_y < 0 or new_y >= config.grid_height:
        return None
    return (new_x, new_y)


def advance_one_step(
    state: GameState,
    config: GameConfig,
    rng: random.Random,
    score_multiplier: int = 1,
    emit: EventEmitter | None = None,
) -> None:
    if state.status != GameStatus.RUNNING:
        return

    if state.pending_direction is not None and not is_opposite(state.direction, state.pending_direction):
        state.direction = state.pending_direction
    state.pending_direction = None

    new_head = _next_head_position(state, config)
    if new_head is None:
        state.status = GameStatus.GAME_OVER
        _emit(emit, GameEventType.PLAYER_DIED, reason="wall", score=state.score)
        return

    if new_head in state.obstacles:
        state.status = GameStatus.GAME_OVER
        _emit(emit, GameEventType.PLAYER_DIED, reason="obstacle", score=state.score)
        return

    will_grow = new_head == state.food
    body_to_check = state.snake if will_grow else state.snake[:-1]
    if new_head in body_to_check:
        state.status = GameStatus.GAME_OVER
        _emit(emit, GameEventType.PLAYER_DIED, reason="self_collision", score=state.score)
        return

    state.snake.insert(0, new_head)

    if will_grow:
        applied_score_multiplier = max(1, score_multiplier)
        state.score += state.score_per_food * applied_score_multiplier
        state.steps_per_second = min(
            state.max_steps_per_second,
            state.steps_per_second + state.speed_increment_per_food,
        )
        _emit(
            emit,
            GameEventType.FOOD_EATEN,
            score=state.score,
            speed=state.steps_per_second,
            score_multiplier=applied_score_multiplier,
        )
        try:
            state.food = spawn_food(
                snake_cells=state.snake,
                obstacle_cells=state.obstacles,
                grid_width=config.grid_width,
                grid_height=config.grid_height,
                rng=rng,
            )
        except RuntimeError:
            state.status = GameStatus.GAME_OVER
            _emit(emit, GameEventType.PLAYER_DIED, reason="board_full", score=state.score)
    else:
        state.snake.pop()


def advance_simulation(
    state: GameState,
    config: GameConfig,
    delta_seconds: float,
    rng: random.Random,
    score_multiplier: int = 1,
    speed_multiplier: float = 1.0,
    emit: EventEmitter | None = None,
) -> int:
    if state.status != GameStatus.RUNNING:
        return 0

    state.accumulator_seconds += max(0.0, delta_seconds)
    steps_taken = 0

    while steps_taken < config.max_steps_per_frame:
        effective_steps_per_second = max(0.1, state.steps_per_second * max(0.1, speed_multiplier))
        step_interval = 1.0 / effective_steps_per_second
        if state.accumulator_seconds < step_interval:
            break
        state.accumulator_seconds -= step_interval
        advance_one_step(state, config, rng, score_multiplier=score_multiplier, emit=emit)
        steps_taken += 1
        head_x, head_y = state.snake[0]
        _emit(
            emit,
            GameEventType.STEP_ADVANCED,
            score=state.score,
            speed=effective_steps_per_second,
            status=state.status.value,
            head_x=head_x,
            head_y=head_y,
        )
        if state.status != GameStatus.RUNNING:
            break

    effective_steps_per_second = max(0.1, state.steps_per_second * max(0.1, speed_multiplier))
    max_carryover = config.max_steps_per_frame * (1.0 / effective_steps_per_second)
    if state.accumulator_seconds > max_carryover:
        state.accumulator_seconds = max_carryover

    return steps_taken
