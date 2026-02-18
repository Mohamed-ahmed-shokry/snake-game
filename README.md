# Snake Game (Pygame) - v2

Snake v2 adds a scene-based flow, settings, difficulty modes, wrap/bounded maps, obstacle mode, persistent high scores, and optional sound.

## Requirements

- Python 3.12+
- `uv` installed

## Setup

```bash
uv sync --group dev
```

## Run

```bash
uv run python main.py
```

## Test

```bash
uv run pytest
```

## Controls

### Menu / Settings / Game Over

- `Up/Down` or `W/S`: Navigate
- `Left/Right` or `A/D`: Change setting values
- `Enter` or `Space`: Select
- `Esc`: Back/Exit depending on screen

### In Game

- `Arrow Keys` or `WASD`: Move snake
- `P` or `Space`: Pause/Resume
- `Esc`: Return to main menu

## Features in v2

- Scene flow: Menu -> Settings -> Play -> Game Over
- Difficulty presets: Easy / Normal / Hard
- Map modes: Bounded / Wrap
- Optional obstacle mode
- Start countdown before movement
- Per-setup high-score leaderboard (top 10)
- Persistent settings and leaderboard in `data/save.json`
- Lightweight generated SFX (mute supported)

## Persistence Notes

- Save file path: `data/save.json`
- If save JSON is corrupted, the game falls back to defaults and attempts to keep a timestamped corrupt backup.
