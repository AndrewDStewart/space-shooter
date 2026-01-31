"""
Space Shooter - A simple arcade-style space shooter game.

Controls:
    Left/Right Arrow Keys: Move ship
    Space: Shoot
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
DARK_GRAY = (100, 100, 100)
LIGHT_GRAY = (200, 200, 200)
RED = (255, 50, 50)
YELLOW = (255, 255, 100)

# Player settings
PLAYER_WIDTH = 50
PLAYER_HEIGHT = 40
PLAYER_SPEED = 7

# Bullet settings
BULLET_WIDTH = 6
BULLET_HEIGHT = 15
BULLET_SPEED = 10
BULLET_COOLDOWN = 15  # Frames between shots

# Asteroid settings - three distinct sizes
ASTEROID_SIZES = {
    "small": {"size": 32, "health": 1, "color": LIGHT_GRAY},
    "medium": {"size": 48, "health": 2, "color": GRAY},
    "large": {"size": 64, "health": 3, "color": DARK_GRAY},
}
ASTEROID_SPEED = 4
ASTEROID_SPAWN_RATE = 60  # Frames between spawns


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


def create_bullet(player_x, player_y):
    """Create a new bullet at the player's position."""
    return {
        "x": player_x + PLAYER_WIDTH // 2 - BULLET_WIDTH // 2,
        "y": player_y,
    }


def draw_bullet(surface, bullet):
    """Draw a bullet as a yellow rectangle."""
    pygame.draw.rect(
        surface,
        YELLOW,
        (bullet["x"], bullet["y"], BULLET_WIDTH, BULLET_HEIGHT)
    )


def create_asteroid():
    """Create a new asteroid at a random x position at the top of the screen."""
    # Randomly choose asteroid size with weighted probability
    size_type = random.choices(
        ["small", "medium", "large"],
        weights=[50, 35, 15],  # Small more common, large rare
        k=1
    )[0]

    size_data = ASTEROID_SIZES[size_type]
    size = size_data["size"]
    x = random.randint(0, SCREEN_WIDTH - size)

    return {
        "x": x,
        "y": -size,
        "size": size,
        "size_type": size_type,
        "health": size_data["health"],
        "max_health": size_data["health"],
        "color": size_data["color"],
    }


def draw_asteroid(surface, asteroid):
    """Draw an asteroid as a rough spherical shape."""
    x, y, size = asteroid["x"], asteroid["y"], asteroid["size"]
    center_x = x + size // 2
    center_y = y + size // 2
    radius = size // 2 - 2

    # Main body (slightly irregular circle using polygon)
    points = []
    num_points = 10
    for i in range(num_points):
        angle = i * (360 / num_points)
        # Slight variation in radius for rocky look
        point_radius = radius - random.randint(0, radius // 5)
        px = center_x + point_radius * pygame.math.Vector2(1, 0).rotate(angle).x
        py = center_y + point_radius * pygame.math.Vector2(1, 0).rotate(angle).y
        points.append((px, py))

    pygame.draw.polygon(surface, asteroid["color"], points)
    pygame.draw.polygon(surface, WHITE, points, 2)  # Outline

    # Show damage with cracks (darker lines) based on health
    damage_taken = asteroid["max_health"] - asteroid["health"]
    if damage_taken > 0:
        # Draw crack lines to show damage
        for i in range(damage_taken):
            crack_start = (center_x + random.randint(-radius//2, radius//2),
                          center_y + random.randint(-radius//2, radius//2))
            crack_end = (center_x + random.randint(-radius//2, radius//2),
                        center_y + random.randint(-radius//2, radius//2))
            pygame.draw.line(surface, BLACK, crack_start, crack_end, 2)


def get_player_rect(player_x, player_y):
    """Get a slightly smaller hitbox for the player (more forgiving collisions)."""
    margin = 8
    return pygame.Rect(
        player_x + margin,
        player_y + margin,
        PLAYER_WIDTH - margin * 2,
        PLAYER_HEIGHT - margin * 2
    )


def get_asteroid_rect(asteroid):
    """Get the hitbox for an asteroid."""
    return pygame.Rect(
        asteroid["x"], asteroid["y"],
        asteroid["size"], asteroid["size"]
    )


def check_player_collision(player_x, player_y, asteroids):
    """Check if the player collides with any asteroid."""
    player_rect = get_player_rect(player_x, player_y)
    for asteroid in asteroids:
        if player_rect.colliderect(get_asteroid_rect(asteroid)):
            return True
    return False


def check_bullet_collisions(bullets, asteroids):
    """Check for bullet-asteroid collisions. Returns updated lists."""
    bullets_to_remove = []
    asteroids_to_remove = []

    for bullet in bullets:
        bullet_rect = pygame.Rect(
            bullet["x"], bullet["y"],
            BULLET_WIDTH, BULLET_HEIGHT
        )
        for asteroid in asteroids:
            if bullet_rect.colliderect(get_asteroid_rect(asteroid)):
                bullets_to_remove.append(bullet)
                asteroid["health"] -= 1
                if asteroid["health"] <= 0:
                    asteroids_to_remove.append(asteroid)
                break  # Bullet can only hit one asteroid

    # Remove destroyed bullets and asteroids
    new_bullets = [b for b in bullets if b not in bullets_to_remove]
    new_asteroids = [a for a in asteroids if a not in asteroids_to_remove]

    return new_bullets, new_asteroids


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
    asteroids = []
    bullets = []
    spawn_timer = 0
    shoot_cooldown = 0
    game_over = False
    return player_x, player_y, asteroids, bullets, spawn_timer, shoot_cooldown, game_over


def main():
    """Main game function."""
    # Set up display
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Space Shooter")
    clock = pygame.time.Clock()

    # Initialize game state
    player_x, player_y, asteroids, bullets, spawn_timer, shoot_cooldown, game_over = reset_game()

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
                    player_x, player_y, asteroids, bullets, spawn_timer, shoot_cooldown, game_over = reset_game()

        if not game_over:
            # Handle continuous key presses for movement and shooting
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                player_x -= PLAYER_SPEED
            if keys[pygame.K_RIGHT]:
                player_x += PLAYER_SPEED

            # Shooting
            if keys[pygame.K_SPACE] and shoot_cooldown <= 0:
                bullets.append(create_bullet(player_x, player_y))
                shoot_cooldown = BULLET_COOLDOWN

            # Decrease shoot cooldown
            if shoot_cooldown > 0:
                shoot_cooldown -= 1

            # Keep player within screen bounds
            if player_x < 0:
                player_x = 0
            if player_x > SCREEN_WIDTH - PLAYER_WIDTH:
                player_x = SCREEN_WIDTH - PLAYER_WIDTH

            # Spawn new asteroids
            spawn_timer += 1
            if spawn_timer >= ASTEROID_SPAWN_RATE:
                asteroids.append(create_asteroid())
                spawn_timer = 0

            # Move asteroids down
            for asteroid in asteroids:
                asteroid["y"] += ASTEROID_SPEED

            # Move bullets up
            for bullet in bullets:
                bullet["y"] -= BULLET_SPEED

            # Remove asteroids and bullets that have moved off screen
            asteroids = [a for a in asteroids if a["y"] < SCREEN_HEIGHT]
            bullets = [b for b in bullets if b["y"] > -BULLET_HEIGHT]

            # Check bullet-asteroid collisions
            bullets, asteroids = check_bullet_collisions(bullets, asteroids)

            # Check for player-asteroid collisions
            if check_player_collision(player_x, player_y, asteroids):
                game_over = True

        # Draw everything
        screen.fill(BLACK)

        # Draw bullets
        for bullet in bullets:
            draw_bullet(screen, bullet)

        # Draw asteroids (use fixed seed per asteroid for consistent shape)
        for asteroid in asteroids:
            random.seed(id(asteroid))
            draw_asteroid(screen, asteroid)
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
