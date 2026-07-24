import pytest

from snake_game.cli import build_parser, config_from_args


def test_cli_builds_config_from_runtime_options() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "--data-file",
            "custom-save.json",
            "--width",
            "400",
            "--height",
            "300",
            "--cell-size",
            "10",
            "--obstacle-count",
            "8",
            "--no-countdown",
        ]
    )

    config = config_from_args(args)

    assert config.data_file == "custom-save.json"
    assert config.window_width == 400
    assert config.window_height == 300
    assert config.cell_size == 10
    assert config.grid_width == 40
    assert config.grid_height == 30
    assert config.obstacle_count == 8
    assert config.countdown_seconds == 0.0


def test_cli_rejects_invalid_board_geometry() -> None:
    parser = build_parser()
    args = parser.parse_args(["--width", "401", "--cell-size", "20"])

    with pytest.raises(ValueError):
        config_from_args(args)
