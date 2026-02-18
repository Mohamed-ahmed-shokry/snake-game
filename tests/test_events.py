import random

from snake_game.config import GameConfig, UserSettings
from snake_game.events import EventBus, GameEvent, GameEventType
from snake_game.logic import advance_one_step, advance_simulation, create_initial_state
from snake_game.systems.progression import StageProgression
from snake_game.types import Direction


def make_config() -> GameConfig:
    config = GameConfig(
        window_width=200,
        window_height=200,
        cell_size=20,
        max_steps_per_frame=3,
        obstacle_count=4,
        stage_points_interval=10,
    )
    config.validate()
    return config


def test_event_bus_emit_and_drain() -> None:
    bus = EventBus()
    bus.emit(GameEvent(type=GameEventType.STEP_ADVANCED))
    events = bus.drain()
    assert len(events) == 1
    assert events[0].type == GameEventType.STEP_ADVANCED
    assert bus.drain() == []


def test_advance_one_step_emits_food_event() -> None:
    config = make_config()
    state = create_initial_state(config, UserSettings(), random.Random(1))
    head_x, head_y = state.snake[0]
    state.food = (head_x + 1, head_y)

    bus = EventBus()
    advance_one_step(state, config, random.Random(1), emit=bus.emit)

    events = bus.drain()
    assert any(event.type == GameEventType.FOOD_EATEN for event in events)


def test_advance_one_step_emits_player_died_event() -> None:
    config = make_config()
    state = create_initial_state(config, UserSettings(), random.Random(2))
    state.snake = [(config.grid_width - 1, 2), (config.grid_width - 2, 2), (config.grid_width - 3, 2)]
    state.direction = Direction.RIGHT
    state.food = (0, 0)

    bus = EventBus()
    advance_one_step(state, config, random.Random(2), emit=bus.emit)

    events = bus.drain()
    death_events = [event for event in events if event.type == GameEventType.PLAYER_DIED]
    assert len(death_events) == 1
    assert death_events[0].payload.get("reason") == "wall"


def test_stage_progression_emits_stage_advanced() -> None:
    progression = StageProgression(points_per_stage=10)
    bus = EventBus()

    changed = progression.update_from_score(22, emit=bus.emit)
    events = bus.drain()

    assert changed is True
    assert progression.current_stage == 3
    assert [event.type for event in events] == [GameEventType.STAGE_ADVANCED, GameEventType.STAGE_ADVANCED]


def test_advance_simulation_emits_step_head_position() -> None:
    config = make_config()
    state = create_initial_state(config, UserSettings(), random.Random(3))
    state.food = (0, 0)
    bus = EventBus()

    advance_simulation(state, config, delta_seconds=0.2, rng=random.Random(3), emit=bus.emit)
    events = bus.drain()
    step_events = [event for event in events if event.type == GameEventType.STEP_ADVANCED]

    assert step_events
    assert "head_x" in step_events[0].payload
    assert "head_y" in step_events[0].payload
