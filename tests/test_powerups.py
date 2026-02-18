import random

from snake_game.systems.powerups import PowerUpSystem, PowerUpType, SpawnedPowerUp


def test_maybe_spawn_places_powerup_in_free_cell() -> None:
    system = PowerUpSystem(
        spawn_chance_per_food=1.0,
        spawn_lifetime_seconds=10.0,
        available_spawn_types=(PowerUpType.SLOW_TIME, PowerUpType.DOUBLE_SCORE),
    )
    occupied = {(0, 0), (1, 0), (2, 0)}

    spawned = system.maybe_spawn(random.Random(1), occupied_cells=occupied, grid_width=4, grid_height=2)

    assert isinstance(spawned, SpawnedPowerUp)
    assert spawned is system.spawned
    assert spawned.position not in occupied
    assert spawned.type in {PowerUpType.SLOW_TIME, PowerUpType.DOUBLE_SCORE}


def test_collect_at_activates_effect_and_clears_spawn() -> None:
    system = PowerUpSystem()
    system.spawned = SpawnedPowerUp(type=PowerUpType.DOUBLE_SCORE, position=(3, 4), remaining_seconds=5.0)

    collected = system.collect_at((3, 4))

    assert collected is not None
    assert collected.type == PowerUpType.DOUBLE_SCORE
    assert system.spawned is None
    assert system.score_multiplier() == system.double_score_multiplier


def test_update_expires_spawn_and_decrements_active_effects() -> None:
    system = PowerUpSystem()
    system.spawned = SpawnedPowerUp(type=PowerUpType.SLOW_TIME, position=(1, 1), remaining_seconds=0.1)
    system.collect_at((1, 1))
    assert system.active_effects
    before = system.active_effects[0].remaining_seconds

    system.update(0.2)

    assert system.spawned is None
    assert system.active_effects
    assert system.active_effects[0].remaining_seconds < before
    assert system.speed_multiplier() == system.slow_time_multiplier


def test_collecting_same_type_refreshes_duration() -> None:
    system = PowerUpSystem()
    system.spawned = SpawnedPowerUp(type=PowerUpType.SLOW_TIME, position=(1, 1), remaining_seconds=5.0)
    first = system.collect_at((1, 1))
    assert first is not None
    first.remaining_seconds = 1.0

    system.spawned = SpawnedPowerUp(type=PowerUpType.SLOW_TIME, position=(2, 2), remaining_seconds=5.0)
    refreshed = system.collect_at((2, 2))

    assert refreshed is first
    assert refreshed.remaining_seconds >= 1.0
    assert len(system.active_effects) == 1


def test_absorb_fatal_collision_consumes_shield() -> None:
    system = PowerUpSystem()
    system.spawned = SpawnedPowerUp(type=PowerUpType.SHIELD, position=(2, 2), remaining_seconds=5.0)
    system.collect_at((2, 2))

    absorbed = system.absorb_fatal_collision("wall")

    assert absorbed is True
    assert system.is_active(PowerUpType.SHIELD) is False


def test_phase_active_flag_reflects_effect_state() -> None:
    system = PowerUpSystem()
    assert system.phase_active() is False

    system.spawned = SpawnedPowerUp(type=PowerUpType.PHASE, position=(3, 1), remaining_seconds=5.0)
    system.collect_at((3, 1))

    assert system.phase_active() is True
