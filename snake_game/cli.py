from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from snake_game import __version__
from snake_game.app import run
from snake_game.config import GameConfig
from snake_game.persistence import export_save_file, import_save_file, reset_save_file


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
    parser.add_argument(
        "--export-save",
        nargs="?",
        const="",
        default=None,
        metavar="DEST",
        help="Export the save file to DEST (default: timestamped file beside the save) and exit.",
    )
    parser.add_argument(
        "--import-save",
        default=None,
        metavar="SRC",
        help="Replace the save file with SRC after validation (backs up the old save) and exit.",
    )
    parser.add_argument(
        "--reset-save",
        action="store_true",
        help="Back up the save file and reset progress to defaults (requires --yes) and exit.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirm a destructive save operation such as --reset-save.",
    )
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


def _data_path_from_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> Path:
    data_file = args.data_file
    if not isinstance(data_file, str) or not data_file.strip():
        parser.error("data_file must not be empty")
    data_path = Path(data_file)
    if data_path.is_dir():
        parser.error("data_file must point to a file, not a directory")
    return data_path


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.export_save is not None or args.import_save is not None or args.reset_save:
        data_path = _data_path_from_args(parser, args)
        try:
            if args.export_save is not None:
                destination = Path(args.export_save) if args.export_save else None
                target = export_save_file(data_path, destination)
                print(f"Exported save to {target}")
            elif args.import_save is not None:
                import_save_file(data_path, Path(args.import_save))
                print(f"Imported save from {args.import_save}")
            elif not args.yes:
                parser.error("--reset-save requires --yes to confirm deleting progress.")
            else:
                backup = reset_save_file(data_path)
                if backup is not None:
                    print(f"Reset save; previous save backed up to {backup}")
                else:
                    print("Reset save; no previous save found.")
        except (OSError, ValueError) as error:
            parser.error(str(error))
        return
    try:
        config = config_from_args(args)
    except ValueError as error:
        parser.error(str(error))
    run(config=config, seed=args.seed)
