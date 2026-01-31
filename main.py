"""
Space Shooter - A simple arcade-style space shooter game.

Controls:
    Left/Right Arrow Keys: Move ship
    ESC: Quit game
    R: Restart after game over
"""

import pygame
import sys
import random

# Initialize Pygame
pygame.init()

# Game constants (9:16 portrait aspect ratio for mobile)
SCREEN_WIDTH = 450
SCREEN_HEIGHT = 800
FPS = 60

# Colors (RGB)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (50, 150, 255)
GRAY = (150, 150, 150)
RED = (255, 50, 50)

# Player settings
PLAYER_WIDTH = 50
PLAYER_HEIGHT = 40
PLAYER_SPEED = 7

# Obstacle settings (scaled for narrower mobile screen)
OBSTACLE_MIN_SIZE = 25
OBSTACLE_MAX_SIZE = 55
OBSTACLE_SPEED = 5
OBSTACLE_SPAWN_RATE = 50  # Lower = more frequent (frames between spawns)


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


def create_obstacle():
    """Create a new obstacle at a random x position at the top of the screen."""
    size = random.randint(OBSTACLE_MIN_SIZE, OBSTACLE_MAX_SIZE)
    x = random.randint(0, SCREEN_WIDTH - size)
    return {"x": x, "y": -size, "size": size}


def draw_obstacle(surface, obstacle):
    """Draw an obstacle as a rough asteroid shape."""
    x, y, size = obstacle["x"], obstacle["y"], obstacle["size"]
    center_x = x + size // 2
    center_y = y + size // 2

    # Draw asteroid as an irregular polygon
    points = []
    for i in range(8):
        angle = i * (360 / 8)
        # Vary the radius for each point to create irregular shape
        radius = size // 2 - random.randint(0, size // 6)
        px = center_x + radius * pygame.math.Vector2(1, 0).rotate(angle).x
        py = center_y + radius * pygame.math.Vector2(1, 0).rotate(angle).y
        points.append((px, py))

    pygame.draw.polygon(surface, GRAY, points)
    pygame.draw.polygon(surface, WHITE, points, 2)  # Outline


def get_player_rect(player_x, player_y):
    """Get a slightly smaller hitbox for the player (more forgiving collisions)."""
    margin = 8
    return pygame.Rect(
        player_x + margin,
        player_y + margin,
        PLAYER_WIDTH - margin * 2,
        PLAYER_HEIGHT - margin * 2
    )


def check_collision(player_x, player_y, obstacles):
    """Check if the player collides with any obstacle."""
    player_rect = get_player_rect(player_x, player_y)
    for obstacle in obstacles:
        obstacle_rect = pygame.Rect(
            obstacle["x"], obstacle["y"],
            obstacle["size"], obstacle["size"]
        )
        if player_rect.colliderect(obstacle_rect):
            return True
    return False


def draw_game_over(surface):
    """Draw the game over screen."""
    font_large = pygame.font.Font(None, 64)
    font_small = pygame.font.Font(None, 28)

    game_over_text = font_large.render("GAME OVER", True, RED)
    restart_text = font_small.render("Press R to restart", True, WHITE)

    surface.blit(
        game_over_text,
        (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, SCREEN_HEIGHT // 2 - 50)
    )
    surface.blit(
        restart_text,
        (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 20)
    )


def reset_game():
    """Reset all game state for a new game."""
    player_x = SCREEN_WIDTH // 2 - PLAYER_WIDTH // 2
    player_y = SCREEN_HEIGHT - PLAYER_HEIGHT - 20
    return player_x, player_y, [], 0, False


def main():
    """Main game function."""
    # Set up display
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Space Shooter")
    clock = pygame.time.Clock()

    # Initialize game state
    player_x, player_y, obstacles, spawn_timer, game_over = reset_game()

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
                elif event.key == pygame.K_r and game_over:
                    # Restart the game
                    player_x, player_y, obstacles, spawn_timer, game_over = reset_game()

        if not game_over:
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

            # Spawn new obstacles
            spawn_timer += 1
            if spawn_timer >= OBSTACLE_SPAWN_RATE:
                obstacles.append(create_obstacle())
                spawn_timer = 0

            # Move obstacles down
            for obstacle in obstacles:
                obstacle["y"] += OBSTACLE_SPEED

            # Remove obstacles that have moved off screen
            obstacles = [obs for obs in obstacles if obs["y"] < SCREEN_HEIGHT]

            # Check for collisions
            if check_collision(player_x, player_y, obstacles):
                game_over = True

        # Draw everything
        screen.fill(BLACK)

        # Draw obstacles (use fixed seed per obstacle for consistent shape)
        for i, obstacle in enumerate(obstacles):
            random.seed(id(obstacle))
            draw_obstacle(screen, obstacle)
        random.seed()  # Reset random seed

        draw_player(screen, player_x, player_y)

        if game_over:
            draw_game_over(screen)

        # Update display
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
