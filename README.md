# Snake Game (Pygame) - v3 (in progress)

Current version includes scene flow, settings, difficulty modes, wrap/bounded maps, obstacle mode, persistent high scores, optional sound, stage progression, and power-up gameplay.

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

## Features

- Scene flow: Menu -> Settings -> Play -> Game Over
- Difficulty presets: Easy / Normal / Hard
- Map modes: Bounded / Wrap
- Optional obstacle mode
- Start countdown before movement
- Per-setup high-score leaderboard (top 10)
- Persistent settings and leaderboard in `data/save.json`
- Lightweight generated SFX (mute supported)
- Stage progression (score-based stage indicator)
- Power-up spawns during runs:
  - `Shield`: absorbs one fatal collision (`wall`, `obstacle`, or `self`)
  - `Phase`: temporarily phases through obstacles and wraps through walls
  - `Slow Time`: temporarily slows snake movement rate
  - `Double Score`: temporarily doubles points from food
- Active power-up timers shown in HUD
- Themed rendering foundation (Neon/Sunset/Ocean) with layered playfield renderer

## Persistence Notes

- Save file path: `data/save.json`
- If save JSON is corrupted, the game falls back to defaults and attempts to keep a timestamped corrupt backup.
