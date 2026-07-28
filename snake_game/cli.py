from __future__ import annotations

import argparse
from collections.abc import Sequence

from snake_game import __version__
from snake_game.app import run
from snake_game.config import GameConfig


def build_parser() -> argparse.ArgumentParser:
    defaults = GameConfig()
    parser = argparse.ArgumentParser(description="Run the Snake game.")
    parser.add_argument("--version", action="version", version=f"Snake Arcade {__version__}")
    parser.add_argument(
        "--data-file", default=defaults.data_file, help="Path to the persistent save JSON file."
    )
    parser.add_argument(
        "--seed", type=int, default=None, help="Seed the game RNG for reproducible runs."
    )
    parser.add_argument(
        "--width", type=int, default=defaults.window_width, help="Window width in pixels."
    )
    parser.add_argument(
        "--height", type=int, default=defaults.window_height, help="Window height in pixels."
    )
    parser.add_argument(
        "--cell-size", type=int, default=defaults.cell_size, help="Grid cell size in pixels."
    )
    parser.add_argument(
        "--obstacle-count",
        type=int,
        default=defaults.obstacle_count,
        help="Number of obstacles used when obstacles are enabled.",
    )
    parser.add_argument("--no-countdown", action="store_true", help="Start gameplay immediately.")
    return parser


def config_from_args(args: argparse.Namespace) -> GameConfig:
    config = GameConfig(
        window_width=args.width,
        window_height=args.height,
        cell_size=args.cell_size,
        obstacle_count=args.obstacle_count,
        data_file=args.data_file,
    )
    if args.no_countdown:
        config.countdown_seconds = 0.0
    config.validate()
    return config


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = config_from_args(args)
    except ValueError as error:
        parser.error(str(error))
    run(config=config, seed=args.seed)
