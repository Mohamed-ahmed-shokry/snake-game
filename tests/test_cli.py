import runpy
from pathlib import Path

import pytest

from snake_game.cli import build_parser, config_from_args, main


def test_cli_builds_config_from_runtime_options() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "--data-file",
            "custom-save.json",
            "--width",
            "1000",
            "--height",
            "700",
            "--cell-size",
            "10",
            "--obstacle-count",
            "8",
            "--no-countdown",
        ]
    )

    config = config_from_args(args)

    assert config.data_file == "custom-save.json"
    assert config.window_width == 1000
    assert config.window_height == 700
    assert config.cell_size == 10
    assert config.grid_width == 100
    assert config.grid_height == 70
    assert config.obstacle_count == 8
    assert config.countdown_seconds == 0.0


def test_cli_rejects_invalid_board_geometry() -> None:
    parser = build_parser()
    args = parser.parse_args(["--width", "401", "--cell-size", "20"])

    with pytest.raises(ValueError):
        config_from_args(args)


def test_cli_rejects_directory_as_data_file(tmp_path: Path) -> None:
    parser = build_parser()
    args = parser.parse_args(["--data-file", str(tmp_path)])

    with pytest.raises(ValueError, match="must point to a file"):
        config_from_args(args)


def test_cli_rejects_empty_data_file() -> None:
    parser = build_parser()
    args = parser.parse_args(["--data-file", " "])

    with pytest.raises(ValueError, match="must not be empty"):
        config_from_args(args)


def test_cli_presents_invalid_configuration_without_a_traceback(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--width", "401"])

    error = capsys.readouterr().err
    assert exit_info.value.code == 2
    assert "window_width must be >= 800" in error
    assert "Traceback" not in error


def test_cli_reports_release_version(capsys: pytest.CaptureFixture[str]) -> None:
    from snake_game import __version__

    parser = build_parser()

    with pytest.raises(SystemExit) as exit_info:
        parser.parse_args(["--version"])

    assert exit_info.value.code == 0
    assert capsys.readouterr().out.strip() == f"Snake Arcade {__version__}"


def test_module_launcher_delegates_to_cli(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[None] = []
    monkeypatch.setattr("snake_game.cli.main", lambda: calls.append(None))

    runpy.run_module("snake_game.__main__", run_name="__main__")

    assert calls == [None]


def test_cli_export_save_creates_timestamped_copy(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from snake_game.persistence import PersistentData, save_persistent_data

    save_path = tmp_path / "save.json"
    save_persistent_data(PersistentData(), save_path)

    main(["--data-file", str(save_path), "--export-save"])

    out = capsys.readouterr().out
    assert "Exported save to" in out
    exports = list(tmp_path.glob("save.json.export-*"))
    assert len(exports) == 1
    assert exports[0].read_bytes() == save_path.read_bytes()


def test_cli_export_save_to_explicit_destination(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from snake_game.persistence import PersistentData, save_persistent_data

    save_path = tmp_path / "save.json"
    save_persistent_data(PersistentData(), save_path)
    dest = tmp_path / "backup.json"

    main(["--data-file", str(save_path), "--export-save", str(dest)])

    assert dest.read_bytes() == save_path.read_bytes()
    assert "Exported save to" in capsys.readouterr().out


def test_cli_export_save_without_save_exits_with_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--data-file", str(tmp_path / "missing.json"), "--export-save"])

    assert exit_info.value.code == 2
    assert "No save file found" in capsys.readouterr().err


def test_cli_import_save_replaces_current_save(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    import json

    from snake_game.persistence import PersistentData, save_persistent_data

    save_path = tmp_path / "save.json"
    save_persistent_data(PersistentData(), save_path)
    source = tmp_path / "other.json"
    source.write_text(json.dumps({"schema_version": 4, "onboarding_seen": True}), encoding="utf-8")

    main(["--data-file", str(save_path), "--import-save", str(source)])

    assert "Imported save from" in capsys.readouterr().out
    assert json.loads(save_path.read_text(encoding="utf-8"))["onboarding_seen"] is True
    assert len(list(tmp_path.glob("save.json.pre-import-*"))) == 1


def test_cli_import_save_rejects_invalid_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from snake_game.persistence import PersistentData, save_persistent_data

    save_path = tmp_path / "save.json"
    save_persistent_data(PersistentData(), save_path)
    bad = tmp_path / "bad.json"
    bad.write_text("{not-json", encoding="utf-8")

    with pytest.raises(SystemExit) as exit_info:
        main(["--data-file", str(save_path), "--import-save", str(bad)])

    assert exit_info.value.code == 2
    assert "not a valid save" in capsys.readouterr().err


def test_cli_reset_save_requires_confirmation(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--data-file", str(tmp_path / "save.json"), "--reset-save"])

    assert exit_info.value.code == 2


def test_cli_reset_save_backs_up_and_resets(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from snake_game.persistence import PersistentData, load_persistent_data, save_persistent_data

    save_path = tmp_path / "save.json"
    save_persistent_data(PersistentData(onboarding_seen=True), save_path)

    main(["--data-file", str(save_path), "--reset-save", "--yes"])

    assert "Reset save; previous save backed up to" in capsys.readouterr().out
    assert load_persistent_data(save_path).onboarding_seen is False
    assert len(list(tmp_path.glob("save.json.pre-reset-*"))) == 1
