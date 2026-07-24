import random

import pytest

from snake_game.systems.hazards import HazardSystem


def test_stage_advance_adds_obstacles_without_using_forbidden_cells() -> None:
    obstacles = {(0, 0)}
    forbidden = {(1, 0), (2, 0), (3, 0)}
    system = HazardSystem(enabled=True, obstacles_per_stage=2)

    added = system.advance_to_stage(
        stage=2,
        obstacles=obstacles,
        forbidden_cells=forbidden,
        grid_width=5,
        grid_height=3,
        rng=random.Random(1),
    )

    assert len(added) == 2
    assert added.isdisjoint(forbidden)
    assert added.issubset(obstacles)
    assert system.last_stage == 2


def test_skipped_stages_add_obstacles_for_each_stage() -> None:
    obstacles: set[tuple[int, int]] = set()
    system = HazardSystem(enabled=True, obstacles_per_stage=2)

    added = system.advance_to_stage(
        stage=4,
        obstacles=obstacles,
        forbidden_cells=set(),
        grid_width=5,
        grid_height=5,
        rng=random.Random(2),
    )

    assert len(added) == 6
    assert len(obstacles) == 6


def test_disabled_hazards_track_stage_without_adding_obstacles() -> None:
    obstacles: set[tuple[int, int]] = set()
    system = HazardSystem(enabled=False)

    added = system.advance_to_stage(
        stage=3,
        obstacles=obstacles,
        forbidden_cells=set(),
        grid_width=4,
        grid_height=4,
        rng=random.Random(3),
    )

    assert added == set()
    assert obstacles == set()
    assert system.last_stage == 3


def test_hazards_reject_negative_obstacle_count() -> None:
    with pytest.raises(ValueError):
        HazardSystem(obstacles_per_stage=-1)
