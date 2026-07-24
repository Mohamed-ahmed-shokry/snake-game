# Snake Arcade

<p align="center">
  <img src="snake_game/assets/snake_arcade_icon.png" alt="Snake Arcade icon" width="160">
</p>

A complete, modern Snake game focused on responsive controls, readable visuals, meaningful progression, and replayable arcade runs.

Version **1.1.0** is a self-contained desktop game with persistent settings, career progress, achievements, per-mode leaderboards, mouse controls, and a polished audiovisual presentation.

## What You Get

- Classic Snake core loop with smooth grid-step movement.
- Multiple run styles:
  - Difficulty presets (`Easy`, `Normal`, `Hard`)
  - Map modes (`Bounded`, `Wrap`)
  - Optional obstacles that expand as stages advance
- Power-ups with real gameplay impact:
  - `Shield`: absorbs one fatal collision
  - `Phase`: pass through obstacles and wrap through walls
  - `Slow Time`: temporary speed slowdown
  - `Double Score`: temporary score multiplier
- Persistent data in `data/save.json`:
  - Settings
  - Graphics preferences
  - Leaderboards for every difficulty/map/obstacle combination
  - Career stats and five achievements
- UI/graphics features:
  - Theme switching (`Neon`, `Sunset`, `Ocean`)
  - Color modes (`off`, `deuteranopia`, `tritanopia`, `high_contrast`)
  - Adjustable text size, grid, particles, reduced motion, and screen shake
  - Distinct power-up symbols and visible active-effect auras
  - Layered scene backgrounds, redesigned HUD, branded window icon, and fullscreen mode
  - Reusable help overlay, click-to-steer, auto-pause, and richer arcade sound cues
  - Progress screen and enhanced game-over summary

## Quick Start

### Requirements

- Python `3.12+`
- `uv`

### Install

```bash
uv sync --group dev
```

### Run

```bash
uv run python main.py
```

You can also launch the package entry point:

```bash
uv run snake-game
uv run python -m snake_game
```

Useful runtime options:

```bash
uv run snake-game --data-file data/dev-save.json --seed 42 --no-countdown
uv run snake-game --width 1000 --height 700 --cell-size 20 --obstacle-count 20
```

### Test

```bash
uv run python -m pytest
```

## Controls

| Context | Keys | Action |
|---|---|---|
| Menus | `Up/Down` or `W/S` | Navigate |
| Menus | `Left/Right` or `A/D` | Change value |
| Menus | `Enter` or `Space` | Select |
| Menus | `Esc` | Back / Exit |
| In game | `Arrow Keys` or `WASD` | Move |
| In game | `P` or `Space` | Pause / Resume |
| In game | `Esc` | Return to menu |
| Anywhere | `M` | Mute / unmute sound |
| Anywhere | `F11` | Toggle fullscreen |

The game also supports mouse navigation in menus and click-to-steer during a run. Losing window focus automatically pauses active gameplay.

## How a Run Progresses

- Eat food to grow, score, and speed up.
- Every 25 points advances the stage.
- When obstacles are enabled, each stage adds new hazards away from the snake, food, and active power-ups.
- Power-ups can absorb a collision, slow time, double score, or phase through walls and obstacles.
- Each completed run updates the matching leaderboard, career totals, and achievement progress.

## Persistence Notes

- Save path: `data/save.json`
- Save schema migration is supported across versions.
- If save data is corrupt, the game falls back to safe defaults and attempts backup.
