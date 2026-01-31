# Space Shooter - Project Conventions

## Overview

A Pygame-based space shooter game. Learning project focused on clean, readable code.

## Project Structure

- `main.py` - Game entry point, contains game loop and all game logic
- `requirements.txt` - Python dependencies (pygame)

## Code Conventions

### Style
- Follow PEP 8 guidelines
- Use descriptive variable names
- Add comments for game logic, not obvious code
- Keep functions focused and small

### Game Architecture
- Game loop runs at 60 FPS
- Use Pygame's clock for frame rate control
- Handle input via event polling and key state checking
- Screen coordinates: (0,0) is top-left, y increases downward

### Constants
- Define at top of file in UPPER_SNAKE_CASE
- Screen dimensions: 800x600
- Colors as RGB tuples

## Running the Game

```bash
python main.py
```

## Development Workflow

1. Make changes
2. Test by running the game
3. Commit at logical milestones with descriptive messages
