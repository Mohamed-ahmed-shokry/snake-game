# Snake Game (Pygame)

A modern Snake build focused on game feel: clean visuals, responsive controls, progression, and replayable runs with power-ups.

This project is currently in the **v4 visual + UX pass**, with ongoing polish to rendering, accessibility, and interface flow.

## What You Get

- Classic Snake core loop with smooth grid-step movement.
- Multiple run styles:
  - Difficulty presets (`Easy`, `Normal`, `Hard`)
  - Map modes (`Bounded`, `Wrap`)
  - Optional obstacles
- Power-ups with real gameplay impact:
  - `Shield`: absorbs one fatal collision
  - `Phase`: pass through obstacles and wrap through walls
  - `Slow Time`: temporary speed slowdown
  - `Double Score`: temporary score multiplier
- Persistent data in `data/save.json`:
  - Settings
  - Graphics preferences
  - Leaderboards
  - Run stats
- UI/graphics features:
  - Theme switching (`Neon`, `Sunset`, `Ocean`)
  - Color modes (`off`, `deuteranopia`, `tritanopia`, `high_contrast`)
  - Grid toggle, particles toggle, reduced motion, screen shake toggle
  - First-run onboarding overlay
  - Enhanced game-over summary

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

### Test

```bash
uv run pytest
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

## Visual and UX Direction

v4 focuses on:

- Stronger readability in motion.
- Better scene hierarchy (menu, settings, play, game-over).
- Cleaner HUD structure with effect timers and stage feedback.
- Accessibility-first options for color and motion sensitivity.

## Persistence Notes

- Save path: `data/save.json`
- Save schema migration is supported across versions.
- If save data is corrupt, the game falls back to safe defaults and attempts backup.

## Development Snapshot

- Rendering is organized around themed, layered playfield drawing.
- Game systems are modular (`progression`, `powerups`, `hazards`).
- Core behavior is covered by automated tests.
