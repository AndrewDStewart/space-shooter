# Space Shooter

A simple space shooter game built with Pygame. Designed for mobile (16:9 landscape) with virtual joystick controls. This is a learning project demonstrating game development fundamentals.

## Features

- Player ship with left/right movement
- Shooting mechanics (spacebar to fire)
- Three asteroid sizes (small, medium, large) with different health
- Asteroids take 1-3 hits to destroy based on size
- Slow obstacles that require navigation:
  - Barricades (indestructible walls)
  - Giant asteroids (128px, 8 hits to destroy)
- Collision detection with game over state
- Clean game loop with consistent frame rate
- Optimized Sprite-based architecture (ready for custom art)

## Requirements

- Python 3.8+
- Pygame 2.5+

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/space-shooter.git
   cd space-shooter
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Game

```bash
python main.py
```

## Controls

### Keyboard
- **Left/Right Arrow**: Move ship
- **Space**: Shoot
- **P** or **ESC**: Pause game
- **R**: Restart after game over
- **F**: Toggle FPS display

### Touch/Mouse
- **Virtual Joystick** (left side): Drag to move ship left/right
- **FIRE** button (right side): Shoot
- **||** button (top-right): Pause
- Tap anywhere to restart after game over

## Project Structure

```
space-shooter/
├── main.py           # Game entry point and main loop
├── requirements.txt  # Python dependencies
├── README.md         # This file
└── CLAUDE.md         # Development conventions
```

## License

MIT License
