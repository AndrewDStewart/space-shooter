# Space Delivery

A delivery game where you navigate through obstacles to complete deliveries safely. Built with Pygame, designed for mobile (16:9 landscape) with virtual joystick controls. This is a learning project demonstrating game development fundamentals.

## Features

- **Delivery scoring system** - Start with $5000, lose money when hit
- **Health system** - Vertical health bar, game over when depleted
- **10-80-10 layout** - Left panel (health + joystick), center play area, right panel (fire button)
- Player ship with left/right movement
- Shooting mechanics (spacebar or fire button)
- Three asteroid sizes with different damage values
- Slow obstacles (barricades, giant asteroids)
- Invincibility frames after taking damage
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
