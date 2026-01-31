"""
Space Shooter - A simple arcade-style space shooter game.

Controls:
    Left/Right Arrow Keys: Move ship
    ESC: Quit game
"""

import pygame
import sys

# Initialize Pygame
pygame.init()

# Game constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors (RGB)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (50, 150, 255)

# Player settings
PLAYER_WIDTH = 50
PLAYER_HEIGHT = 40
PLAYER_SPEED = 7


def draw_player(surface, x, y):
    """Draw the player ship as a simple triangle."""
    # Ship body (triangle pointing up)
    points = [
        (x + PLAYER_WIDTH // 2, y),  # Top point
        (x, y + PLAYER_HEIGHT),       # Bottom left
        (x + PLAYER_WIDTH, y + PLAYER_HEIGHT)  # Bottom right
    ]
    pygame.draw.polygon(surface, BLUE, points)

    # Cockpit detail
    pygame.draw.circle(
        surface,
        WHITE,
        (x + PLAYER_WIDTH // 2, y + PLAYER_HEIGHT // 2 + 5),
        8
    )


def main():
    """Main game function."""
    # Set up display
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Space Shooter")
    clock = pygame.time.Clock()

    # Player starting position (centered at bottom)
    player_x = SCREEN_WIDTH // 2 - PLAYER_WIDTH // 2
    player_y = SCREEN_HEIGHT - PLAYER_HEIGHT - 20

    # Game loop
    running = True
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # Handle continuous key presses for movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            player_x -= PLAYER_SPEED
        if keys[pygame.K_RIGHT]:
            player_x += PLAYER_SPEED

        # Keep player within screen bounds
        if player_x < 0:
            player_x = 0
        if player_x > SCREEN_WIDTH - PLAYER_WIDTH:
            player_x = SCREEN_WIDTH - PLAYER_WIDTH

        # Draw everything
        screen.fill(BLACK)
        draw_player(screen, player_x, player_y)

        # Update display
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
