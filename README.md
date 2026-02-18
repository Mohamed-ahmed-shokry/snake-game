# Snake Game (Pygame)

Classic grid-based Snake built with Pygame.

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

- `Arrow Keys` or `WASD`: Move snake
- `P` or `Space`: Pause/Resume
- `R`: Restart after game over
- `Esc`: Quit

## Rules

- Snake moves on fixed grid steps using accumulated delta timing.
- Hitting a wall ends the game.
- Hitting your own body ends the game.
- Immediate reverse direction input is ignored.
- Eating food increases score and snake speed (up to a cap).

## Out of Scope in v1

- Audio
- Obstacles/levels
- Difficulty menu
- Save/high-score persistence
- EXE packaging
