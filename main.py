"""
Space Shooter - A simple arcade-style space shooter game.

Controls:
    Left/Right Arrow Keys: Move ship
    Space: Shoot
    ESC: Quit game
    R: Restart after game over
    F: Toggle FPS display
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
BROWN = (139, 90, 43)
DARK_BROWN = (101, 67, 33)
GREEN = (50, 255, 50)

# Player settings
PLAYER_WIDTH = 50
PLAYER_HEIGHT = 40
PLAYER_SPEED = 7
PLAYER_HITBOX_MARGIN = 8

# Bullet settings
BULLET_WIDTH = 6
BULLET_HEIGHT = 15
BULLET_SPEED = 10
BULLET_COOLDOWN = 15

# Asteroid settings
ASTEROID_SIZES = {
    "small": {"size": 32, "health": 1, "color": LIGHT_GRAY},
    "medium": {"size": 48, "health": 2, "color": GRAY},
    "large": {"size": 64, "health": 3, "color": DARK_GRAY},
}
ASTEROID_SPEED = 4
ASTEROID_SPAWN_RATE = 60

# Slow obstacle settings
OBSTACLE_SPEED = 2
OBSTACLE_SPAWN_RATE = 180

# Barricade settings
BARRICADE_WIDTH = 64
BARRICADE_HEIGHT = 16

# Giant asteroid settings
GIANT_ASTEROID_SIZE = 128
GIANT_ASTEROID_HEALTH = 8


# --- Sprite Classes ---

class Player(pygame.sprite.Sprite):
    """Player ship sprite."""

    def __init__(self):
        super().__init__()
        # Pre-render the player image
        self.image = pygame.Surface((PLAYER_WIDTH, PLAYER_HEIGHT), pygame.SRCALPHA)
        self._draw_ship()
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 20
        # Smaller hitbox for forgiving collisions
        self.hitbox = self.rect.inflate(-PLAYER_HITBOX_MARGIN * 2, -PLAYER_HITBOX_MARGIN * 2)
        self.shoot_cooldown = 0

    def _draw_ship(self):
        """Draw the ship onto the sprite's surface."""
        points = [
            (PLAYER_WIDTH // 2, 0),
            (0, PLAYER_HEIGHT),
            (PLAYER_WIDTH, PLAYER_HEIGHT)
        ]
        pygame.draw.polygon(self.image, BLUE, points)
        pygame.draw.circle(self.image, WHITE, (PLAYER_WIDTH // 2, PLAYER_HEIGHT // 2 + 5), 8)

    def update(self, keys):
        """Update player position based on input."""
        if keys[pygame.K_LEFT]:
            self.rect.x -= PLAYER_SPEED
        if keys[pygame.K_RIGHT]:
            self.rect.x += PLAYER_SPEED

        # Keep within bounds
        self.rect.clamp_ip(pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
        self.hitbox.center = self.rect.center

        # Cooldown timer
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def can_shoot(self):
        return self.shoot_cooldown <= 0

    def shoot(self):
        self.shoot_cooldown = BULLET_COOLDOWN
        return Bullet(self.rect.centerx, self.rect.top)


class Bullet(pygame.sprite.Sprite):
    """Bullet sprite."""

    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((BULLET_WIDTH, BULLET_HEIGHT))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect(centerx=x, bottom=y)

    def update(self):
        self.rect.y -= BULLET_SPEED
        if self.rect.bottom < 0:
            self.kill()


class Asteroid(pygame.sprite.Sprite):
    """Regular asteroid sprite (small, medium, large)."""

    def __init__(self, size_type=None):
        super().__init__()

        # Choose size randomly if not specified
        if size_type is None:
            size_type = random.choices(
                ["small", "medium", "large"],
                weights=[50, 35, 15],
                k=1
            )[0]

        size_data = ASTEROID_SIZES[size_type]
        self.size = size_data["size"]
        self.health = size_data["health"]
        self.max_health = size_data["health"]
        self.color = size_data["color"]
        self.speed = ASTEROID_SPEED

        # Pre-render the asteroid shape
        self.base_image = self._create_asteroid_surface()
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, SCREEN_WIDTH - self.size)
        self.rect.bottom = 0

    def _create_asteroid_surface(self):
        """Pre-render asteroid shape to a surface."""
        surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        center = self.size // 2
        radius = self.size // 2 - 2

        # Generate irregular polygon points once
        points = []
        num_points = 10
        for i in range(num_points):
            angle = i * (360 / num_points)
            point_radius = radius - random.randint(0, radius // 5)
            px = center + point_radius * pygame.math.Vector2(1, 0).rotate(angle).x
            py = center + point_radius * pygame.math.Vector2(1, 0).rotate(angle).y
            points.append((px, py))

        pygame.draw.polygon(surface, self.color, points)
        pygame.draw.polygon(surface, WHITE, points, 2)
        return surface

    def _add_damage_cracks(self):
        """Add crack effects based on damage taken."""
        self.image = self.base_image.copy()
        damage = self.max_health - self.health
        center = self.size // 2
        radius = self.size // 2 - 2

        for _ in range(damage):
            crack_start = (center + random.randint(-radius//2, radius//2),
                          center + random.randint(-radius//2, radius//2))
            crack_end = (center + random.randint(-radius//2, radius//2),
                        center + random.randint(-radius//2, radius//2))
            pygame.draw.line(self.image, BLACK, crack_start, crack_end, 2)

    def take_damage(self):
        """Take one point of damage. Returns True if destroyed."""
        self.health -= 1
        if self.health <= 0:
            self.kill()
            return True
        self._add_damage_cracks()
        return False

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()


class Barricade(pygame.sprite.Sprite):
    """Indestructible wall obstacle."""

    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((BARRICADE_WIDTH, BARRICADE_HEIGHT))
        self._draw_barricade()
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, SCREEN_WIDTH - BARRICADE_WIDTH)
        self.rect.bottom = 0
        self.indestructible = True

    def _draw_barricade(self):
        """Pre-render barricade."""
        self.image.fill(BROWN)
        # Metal rivets
        for rx in range(6, BARRICADE_WIDTH - 6, 12):
            pygame.draw.circle(self.image, DARK_BROWN, (rx, BARRICADE_HEIGHT // 2), 3)
        pygame.draw.rect(self.image, WHITE, (0, 0, BARRICADE_WIDTH, BARRICADE_HEIGHT), 2)

    def update(self):
        self.rect.y += OBSTACLE_SPEED
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()


class GiantAsteroid(pygame.sprite.Sprite):
    """Large slow-moving asteroid."""

    def __init__(self):
        super().__init__()
        self.size = GIANT_ASTEROID_SIZE
        self.health = GIANT_ASTEROID_HEALTH
        self.max_health = GIANT_ASTEROID_HEALTH
        self.indestructible = False

        self.base_image = self._create_surface()
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, SCREEN_WIDTH - self.size)
        self.rect.bottom = 0

    def _create_surface(self):
        """Pre-render giant asteroid."""
        surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        center = self.size // 2
        radius = self.size // 2 - 4

        # Irregular circle
        points = []
        for i in range(12):
            angle = i * (360 / 12)
            point_radius = radius - random.randint(0, radius // 6)
            px = center + point_radius * pygame.math.Vector2(1, 0).rotate(angle).x
            py = center + point_radius * pygame.math.Vector2(1, 0).rotate(angle).y
            points.append((px, py))

        pygame.draw.polygon(surface, DARK_GRAY, points)
        pygame.draw.polygon(surface, WHITE, points, 3)

        # Craters
        for _ in range(3):
            cx = center + random.randint(-radius//2, radius//2)
            cy = center + random.randint(-radius//2, radius//2)
            cr = random.randint(8, 15)
            pygame.draw.circle(surface, GRAY, (cx, cy), cr)
            pygame.draw.circle(surface, DARK_GRAY, (cx, cy), cr, 2)

        return surface

    def _add_damage_cracks(self):
        """Add crack effects based on damage taken."""
        self.image = self.base_image.copy()
        damage = self.max_health - self.health
        center = self.size // 2
        radius = self.size // 2 - 4

        for _ in range(min(damage, 6)):
            crack_start = (center + random.randint(-radius//2, radius//2),
                          center + random.randint(-radius//2, radius//2))
            crack_end = (center + random.randint(-radius//2, radius//2),
                        center + random.randint(-radius//2, radius//2))
            pygame.draw.line(self.image, BLACK, crack_start, crack_end, 3)

    def take_damage(self):
        """Take one point of damage. Returns True if destroyed."""
        self.health -= 1
        if self.health <= 0:
            self.kill()
            return True
        self._add_damage_cracks()
        return False

    def update(self):
        self.rect.y += OBSTACLE_SPEED
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()


# --- Game Class ---

class Game:
    """Main game class managing all state and logic."""

    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Space Shooter")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 28)
        self.font_large = pygame.font.Font(None, 64)
        self.show_fps = True
        self.reset()

    def reset(self):
        """Reset game state for a new game."""
        # Sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.asteroids = pygame.sprite.Group()
        self.obstacles = pygame.sprite.Group()

        # Player
        self.player = Player()
        self.all_sprites.add(self.player)

        # Timers
        self.asteroid_timer = 0
        self.obstacle_timer = 0

        # State
        self.game_over = False

    def spawn_asteroid(self):
        """Spawn a new asteroid."""
        asteroid = Asteroid()
        self.asteroids.add(asteroid)
        self.all_sprites.add(asteroid)

    def spawn_obstacle(self):
        """Spawn a barricade or giant asteroid."""
        if random.random() < 0.5:
            obstacle = Barricade()
        else:
            obstacle = GiantAsteroid()
        self.obstacles.add(obstacle)
        self.all_sprites.add(obstacle)

    def handle_collisions(self):
        """Handle all collision detection."""
        # Bullets vs Asteroids
        hits = pygame.sprite.groupcollide(self.bullets, self.asteroids, True, False)
        for bullet, hit_asteroids in hits.items():
            for asteroid in hit_asteroids:
                asteroid.take_damage()

        # Bullets vs Obstacles
        for bullet in self.bullets:
            hit_obstacles = pygame.sprite.spritecollide(bullet, self.obstacles, False)
            for obstacle in hit_obstacles:
                bullet.kill()
                if hasattr(obstacle, 'take_damage'):
                    obstacle.take_damage()

        # Player vs Asteroids
        if pygame.sprite.spritecollide(self.player, self.asteroids, False,
                                        collided=lambda p, a: p.hitbox.colliderect(a.rect)):
            self.game_over = True

        # Player vs Obstacles
        if pygame.sprite.spritecollide(self.player, self.obstacles, False,
                                        collided=lambda p, o: p.hitbox.colliderect(o.rect)):
            self.game_over = True

    def update(self):
        """Update game state."""
        if self.game_over:
            return

        keys = pygame.key.get_pressed()

        # Update player
        self.player.update(keys)

        # Shooting
        if keys[pygame.K_SPACE] and self.player.can_shoot():
            bullet = self.player.shoot()
            self.bullets.add(bullet)
            self.all_sprites.add(bullet)

        # Update all sprites
        self.bullets.update()
        self.asteroids.update()
        self.obstacles.update()

        # Spawn timers
        self.asteroid_timer += 1
        if self.asteroid_timer >= ASTEROID_SPAWN_RATE:
            self.spawn_asteroid()
            self.asteroid_timer = 0

        self.obstacle_timer += 1
        if self.obstacle_timer >= OBSTACLE_SPAWN_RATE:
            self.spawn_obstacle()
            self.obstacle_timer = 0

        # Collisions
        self.handle_collisions()

    def draw(self):
        """Draw everything to the screen."""
        self.screen.fill(BLACK)
        self.all_sprites.draw(self.screen)

        # FPS display
        if self.show_fps:
            fps = int(self.clock.get_fps())
            color = GREEN if fps >= 55 else YELLOW if fps >= 30 else RED
            fps_text = self.font.render(f"FPS: {fps}", True, color)
            self.screen.blit(fps_text, (10, 10))

        # Game over screen
        if self.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            self.screen.blit(overlay, (0, 0))

            text = self.font_large.render("GAME OVER", True, RED)
            self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2,
                                    SCREEN_HEIGHT // 2 - 50))

            restart_text = self.font.render("Press R to restart", True, WHITE)
            self.screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2,
                                            SCREEN_HEIGHT // 2 + 20))

        pygame.display.flip()

    def run(self):
        """Main game loop."""
        running = True
        while running:
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r and self.game_over:
                        self.reset()
                    elif event.key == pygame.K_f:
                        self.show_fps = not self.show_fps

            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


def main():
    """Entry point."""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
