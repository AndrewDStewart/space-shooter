"""
Space Delivery - A delivery game where you navigate obstacles to complete deliveries.

Controls:
    Keyboard:
        Left/Right Arrow Keys: Move ship
        Space: Shoot
        P or ESC: Pause game
        R: Restart after game over
        F: Toggle FPS display

    Touch/Mouse:
        Virtual joystick (left panel): Move ship
        Fire button (right panel): Shoot
        Pause button: Pause game
"""

import pygame
import sys
import random
import math

# Initialize Pygame
pygame.init()

# Game constants (16:9 landscape aspect ratio for mobile)
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 450
FPS = 60

# Layout zones (10% - 80% - 10%)
LEFT_PANEL_WIDTH = 80   # 10% for joystick + health bar
RIGHT_PANEL_WIDTH = 80  # 10% for fire button
PLAY_AREA_X = LEFT_PANEL_WIDTH
PLAY_AREA_WIDTH = SCREEN_WIDTH - LEFT_PANEL_WIDTH - RIGHT_PANEL_WIDTH  # 640px (80%)

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
DARK_GREEN = (30, 150, 30)
PANEL_BG = (20, 20, 30)

# Player settings
PLAYER_WIDTH = 50
PLAYER_HEIGHT = 40
PLAYER_SPEED = 7
PLAYER_HITBOX_MARGIN = 8
PLAYER_MAX_HEALTH = 100
PLAYER_START_SCORE = 5000

# Damage values
ASTEROID_DAMAGE = 15
BARRICADE_DAMAGE = 25
GIANT_ASTEROID_DAMAGE = 30
SCORE_LOSS_MULTIPLIER = 10  # Score lost = damage * this

# Bullet settings
BULLET_WIDTH = 6
BULLET_HEIGHT = 15
BULLET_SPEED = 10
BULLET_COOLDOWN = 15

# Asteroid settings
ASTEROID_SIZES = {
    "small": {"size": 32, "health": 1, "color": LIGHT_GRAY, "damage": 10},
    "medium": {"size": 48, "health": 2, "color": GRAY, "damage": 15},
    "large": {"size": 64, "health": 3, "color": DARK_GRAY, "damage": 20},
}
ASTEROID_SPEED = 4
ASTEROID_SPAWN_RATE = 60

# Slow obstacle settings
OBSTACLE_SPEED = 2
OBSTACLE_SPAWN_RATE = 180

# Barricade settings (wide horizontal walls)
BARRICADE_WIDTH = 64
BARRICADE_HEIGHT = 16

# Giant asteroid settings
GIANT_ASTEROID_SIZE = 100
GIANT_ASTEROID_HEALTH = 8

# Touch control settings
JOYSTICK_RADIUS = 30  # Smaller to fit in panel
JOYSTICK_KNOB_RADIUS = 12
JOYSTICK_DEAD_ZONE = 5
TOUCH_BUTTON_ALPHA = 150

# Invincibility after hit (frames)
INVINCIBILITY_FRAMES = 60


# --- UI Classes ---

class HealthBar:
    """Vertical health bar display."""

    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.border_width = 2

    def draw(self, surface, current_health, max_health):
        """Draw the health bar."""
        # Background
        pygame.draw.rect(surface, DARK_GRAY, self.rect)

        # Health fill (from bottom up)
        health_ratio = max(0, current_health / max_health)
        fill_height = int((self.rect.height - self.border_width * 2) * health_ratio)
        fill_rect = pygame.Rect(
            self.rect.x + self.border_width,
            self.rect.bottom - self.border_width - fill_height,
            self.rect.width - self.border_width * 2,
            fill_height
        )

        # Color based on health level
        if health_ratio > 0.6:
            color = GREEN
        elif health_ratio > 0.3:
            color = YELLOW
        else:
            color = RED

        if fill_height > 0:
            pygame.draw.rect(surface, color, fill_rect)

        # Border
        pygame.draw.rect(surface, WHITE, self.rect, self.border_width)


class VirtualJoystick:
    """A virtual joystick for touch/mouse control."""

    def __init__(self, center_x, center_y):
        self.center = pygame.math.Vector2(center_x, center_y)
        self.knob_pos = pygame.math.Vector2(center_x, center_y)
        self.active = False
        self.value_x = 0

    def update(self, mouse_pressed, mouse_pos):
        """Update joystick based on input."""
        mouse_vec = pygame.math.Vector2(mouse_pos)
        distance_to_center = self.center.distance_to(mouse_vec)

        if mouse_pressed:
            if distance_to_center <= JOYSTICK_RADIUS * 2 or self.active:
                self.active = True
                offset = mouse_vec - self.center

                if offset.length() > JOYSTICK_RADIUS:
                    offset.scale_to_length(JOYSTICK_RADIUS)

                self.knob_pos = self.center + offset

                if abs(offset.x) > JOYSTICK_DEAD_ZONE:
                    self.value_x = offset.x / JOYSTICK_RADIUS
                else:
                    self.value_x = 0
        else:
            self.active = False
            self.knob_pos = self.center.copy()
            self.value_x = 0

    def draw(self, surface):
        """Draw the joystick."""
        # Outer ring
        pygame.draw.circle(surface, GRAY, (int(self.center.x), int(self.center.y)),
                          JOYSTICK_RADIUS, 2)

        # Inner knob
        knob_color = BLUE if self.active else DARK_GRAY
        pygame.draw.circle(surface, knob_color,
                          (int(self.knob_pos.x), int(self.knob_pos.y)),
                          JOYSTICK_KNOB_RADIUS)
        pygame.draw.circle(surface, WHITE,
                          (int(self.knob_pos.x), int(self.knob_pos.y)),
                          JOYSTICK_KNOB_RADIUS, 2)

    @property
    def moving_left(self):
        return self.value_x < -0.3

    @property
    def moving_right(self):
        return self.value_x > 0.3


class TouchButton:
    """A touchable on-screen button."""

    def __init__(self, x, y, width, height, label, color=WHITE, radius=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.color = color
        self.pressed = False
        self.font = pygame.font.Font(None, 24)
        self.radius = radius

    def draw(self, surface):
        """Draw the button."""
        if self.radius:
            color = self.color if not self.pressed else WHITE
            pygame.draw.circle(surface, color,
                             self.rect.center, self.radius)
            pygame.draw.circle(surface, WHITE,
                             self.rect.center, self.radius, 2)
        else:
            color = self.color if not self.pressed else WHITE
            pygame.draw.rect(surface, color, self.rect, border_radius=5)
            pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=5)

        text = self.font.render(self.label, True, BLACK if self.pressed else WHITE)
        text_rect = text.get_rect(center=self.rect.center)
        surface.blit(text, text_rect)

    def check_press(self, pos):
        """Check if position is within button."""
        if self.radius:
            center = pygame.math.Vector2(self.rect.center)
            return center.distance_to(pygame.math.Vector2(pos)) <= self.radius
        return self.rect.collidepoint(pos)


class TouchControls:
    """Manages all on-screen touch controls."""

    def __init__(self):
        # Joystick in left panel (bottom)
        joystick_y = SCREEN_HEIGHT - JOYSTICK_RADIUS - 20
        self.joystick = VirtualJoystick(
            LEFT_PANEL_WIDTH // 2,
            joystick_y
        )

        # Fire button in right panel (centered vertically)
        fire_radius = 30
        self.fire_btn = TouchButton(
            SCREEN_WIDTH - RIGHT_PANEL_WIDTH // 2 - fire_radius,
            SCREEN_HEIGHT // 2 - fire_radius,
            fire_radius * 2, fire_radius * 2,
            "FIRE", RED, radius=fire_radius
        )

        # Pause button (top of right panel)
        pause_size = 30
        self.pause_btn = TouchButton(
            SCREEN_WIDTH - RIGHT_PANEL_WIDTH // 2 - pause_size // 2,
            10,
            pause_size, pause_size,
            "||", GRAY
        )

    def update(self, mouse_pressed, mouse_pos):
        """Update controls based on input."""
        self.joystick.update(mouse_pressed, mouse_pos)

        if mouse_pressed:
            self.fire_btn.pressed = self.fire_btn.check_press(mouse_pos)
        else:
            self.fire_btn.pressed = False

    def check_pause_tap(self, pos):
        """Check if pause button was tapped."""
        return self.pause_btn.check_press(pos)

    def draw(self, surface):
        """Draw all touch controls."""
        self.joystick.draw(surface)
        self.fire_btn.draw(surface)
        self.pause_btn.draw(surface)

    @property
    def moving_left(self):
        return self.joystick.moving_left

    @property
    def moving_right(self):
        return self.joystick.moving_right

    @property
    def firing(self):
        return self.fire_btn.pressed


class PauseMenu:
    """Pause menu overlay."""

    def __init__(self):
        self.font_large = pygame.font.Font(None, 64)
        self.font_medium = pygame.font.Font(None, 40)

        btn_width = 200
        btn_height = 50
        btn_x = SCREEN_WIDTH // 2 - btn_width // 2
        center_y = SCREEN_HEIGHT // 2

        self.resume_btn = TouchButton(btn_x, center_y - 30, btn_width, btn_height, "RESUME", GREEN)
        self.resume_btn.font = self.font_medium

        self.quit_btn = TouchButton(btn_x, center_y + 40, btn_width, btn_height, "QUIT", RED)
        self.quit_btn.font = self.font_medium

    def draw(self, surface):
        """Draw the pause menu."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        title = self.font_large.render("PAUSED", True, WHITE)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - 100))

        self.resume_btn.draw(surface)
        self.quit_btn.draw(surface)

    def handle_click(self, pos):
        """Handle click on menu."""
        if self.resume_btn.check_press(pos):
            return 'resume'
        elif self.quit_btn.check_press(pos):
            return 'quit'
        return None


# --- Sprite Classes ---

class Player(pygame.sprite.Sprite):
    """Player ship sprite."""

    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((PLAYER_WIDTH, PLAYER_HEIGHT), pygame.SRCALPHA)
        self._draw_ship()
        self.rect = self.image.get_rect()
        self.rect.centerx = PLAY_AREA_X + PLAY_AREA_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 20
        self.hitbox = self.rect.inflate(-PLAYER_HITBOX_MARGIN * 2, -PLAYER_HITBOX_MARGIN * 2)
        self.shoot_cooldown = 0
        self.invincible = 0  # Invincibility frames after hit

    def _draw_ship(self):
        """Draw the ship."""
        points = [
            (PLAYER_WIDTH // 2, 0),
            (0, PLAYER_HEIGHT),
            (PLAYER_WIDTH, PLAYER_HEIGHT)
        ]
        pygame.draw.polygon(self.image, BLUE, points)
        pygame.draw.circle(self.image, WHITE, (PLAYER_WIDTH // 2, PLAYER_HEIGHT // 2 + 5), 8)

    def update(self, keys, touch_left=False, touch_right=False):
        """Update player position."""
        if keys[pygame.K_LEFT] or touch_left:
            self.rect.x -= PLAYER_SPEED
        if keys[pygame.K_RIGHT] or touch_right:
            self.rect.x += PLAYER_SPEED

        # Keep within play area bounds
        play_bounds = pygame.Rect(PLAY_AREA_X, 0, PLAY_AREA_WIDTH, SCREEN_HEIGHT)
        self.rect.clamp_ip(play_bounds)
        self.hitbox.center = self.rect.center

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        if self.invincible > 0:
            self.invincible -= 1

    def take_hit(self):
        """Called when player is hit. Returns True if should take damage."""
        if self.invincible > 0:
            return False
        self.invincible = INVINCIBILITY_FRAMES
        return True

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
    """Regular asteroid sprite."""

    def __init__(self, size_type=None):
        super().__init__()

        if size_type is None:
            size_type = random.choices(["small", "medium", "large"], weights=[50, 35, 15], k=1)[0]

        size_data = ASTEROID_SIZES[size_type]
        self.size = size_data["size"]
        self.health = size_data["health"]
        self.max_health = size_data["health"]
        self.color = size_data["color"]
        self.damage = size_data["damage"]
        self.speed = ASTEROID_SPEED

        self.base_image = self._create_asteroid_surface()
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect()
        # Spawn within play area
        self.rect.x = random.randint(PLAY_AREA_X, PLAY_AREA_X + PLAY_AREA_WIDTH - self.size)
        self.rect.bottom = 0

    def _create_asteroid_surface(self):
        """Pre-render asteroid shape."""
        surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        center = self.size // 2
        radius = self.size // 2 - 2

        points = []
        for i in range(10):
            angle = i * 36
            point_radius = radius - random.randint(0, radius // 5)
            px = center + point_radius * pygame.math.Vector2(1, 0).rotate(angle).x
            py = center + point_radius * pygame.math.Vector2(1, 0).rotate(angle).y
            points.append((px, py))

        pygame.draw.polygon(surface, self.color, points)
        pygame.draw.polygon(surface, WHITE, points, 2)
        return surface

    def _add_damage_cracks(self):
        """Add crack effects."""
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
        """Take damage. Returns True if destroyed."""
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
        self.rect.x = random.randint(PLAY_AREA_X, PLAY_AREA_X + PLAY_AREA_WIDTH - BARRICADE_WIDTH)
        self.rect.bottom = 0
        self.indestructible = True
        self.damage = BARRICADE_DAMAGE

    def _draw_barricade(self):
        """Pre-render barricade."""
        self.image.fill(BROWN)
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
        self.damage = GIANT_ASTEROID_DAMAGE

        self.base_image = self._create_surface()
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(PLAY_AREA_X, PLAY_AREA_X + PLAY_AREA_WIDTH - self.size)
        self.rect.bottom = 0

    def _create_surface(self):
        """Pre-render giant asteroid."""
        surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        center = self.size // 2
        radius = self.size // 2 - 4

        points = []
        for i in range(12):
            angle = i * 30
            point_radius = radius - random.randint(0, radius // 6)
            px = center + point_radius * pygame.math.Vector2(1, 0).rotate(angle).x
            py = center + point_radius * pygame.math.Vector2(1, 0).rotate(angle).y
            points.append((px, py))

        pygame.draw.polygon(surface, DARK_GRAY, points)
        pygame.draw.polygon(surface, WHITE, points, 3)

        for _ in range(3):
            cx = center + random.randint(-radius//2, radius//2)
            cy = center + random.randint(-radius//2, radius//2)
            cr = random.randint(6, 12)
            pygame.draw.circle(surface, GRAY, (cx, cy), cr)
            pygame.draw.circle(surface, DARK_GRAY, (cx, cy), cr, 2)

        return surface

    def _add_damage_cracks(self):
        """Add crack effects."""
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
        """Take damage. Returns True if destroyed."""
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
    """Main game class."""

    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Space Delivery")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 28)
        self.font_large = pygame.font.Font(None, 64)
        self.font_score = pygame.font.Font(None, 36)
        self.show_fps = False

        self.touch_controls = TouchControls()
        self.pause_menu = PauseMenu()

        # Health bar in left panel (above joystick)
        health_bar_height = SCREEN_HEIGHT - 120  # Leave room for joystick
        self.health_bar = HealthBar(10, 10, LEFT_PANEL_WIDTH - 20, health_bar_height)

        self.reset()

    def reset(self):
        """Reset game state."""
        self.all_sprites = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.asteroids = pygame.sprite.Group()
        self.obstacles = pygame.sprite.Group()

        self.player = Player()
        self.all_sprites.add(self.player)

        self.asteroid_timer = 0
        self.obstacle_timer = 0

        self.health = PLAYER_MAX_HEALTH
        self.score = PLAYER_START_SCORE

        self.game_over = False
        self.paused = False

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
        hit_asteroids = pygame.sprite.spritecollide(
            self.player, self.asteroids, True,
            collided=lambda p, a: p.hitbox.colliderect(a.rect)
        )
        for asteroid in hit_asteroids:
            if self.player.take_hit():
                damage = asteroid.damage
                self.health -= damage
                self.score -= damage * SCORE_LOSS_MULTIPLIER

        # Player vs Obstacles
        hit_obstacles = pygame.sprite.spritecollide(
            self.player, self.obstacles, False,
            collided=lambda p, o: p.hitbox.colliderect(o.rect)
        )
        for obstacle in hit_obstacles:
            if self.player.take_hit():
                damage = obstacle.damage
                self.health -= damage
                self.score -= damage * SCORE_LOSS_MULTIPLIER

        # Check for game over
        if self.health <= 0:
            self.health = 0
            self.game_over = True

        # Keep score from going negative
        if self.score < 0:
            self.score = 0

    def toggle_pause(self):
        """Toggle pause state."""
        if not self.game_over:
            self.paused = not self.paused

    def update(self):
        """Update game state."""
        if self.game_over or self.paused:
            return

        keys = pygame.key.get_pressed()

        mouse_pressed = pygame.mouse.get_pressed()[0]
        mouse_pos = pygame.mouse.get_pos()
        self.touch_controls.update(mouse_pressed, mouse_pos)

        self.player.update(
            keys,
            touch_left=self.touch_controls.moving_left,
            touch_right=self.touch_controls.moving_right
        )

        shooting = keys[pygame.K_SPACE] or self.touch_controls.firing
        if shooting and self.player.can_shoot():
            bullet = self.player.shoot()
            self.bullets.add(bullet)
            self.all_sprites.add(bullet)

        self.bullets.update()
        self.asteroids.update()
        self.obstacles.update()

        self.asteroid_timer += 1
        if self.asteroid_timer >= ASTEROID_SPAWN_RATE:
            self.spawn_asteroid()
            self.asteroid_timer = 0

        self.obstacle_timer += 1
        if self.obstacle_timer >= OBSTACLE_SPAWN_RATE:
            self.spawn_obstacle()
            self.obstacle_timer = 0

        self.handle_collisions()

    def draw(self):
        """Draw everything to the screen."""
        # Clear screen
        self.screen.fill(BLACK)

        # Draw panel backgrounds
        pygame.draw.rect(self.screen, PANEL_BG, (0, 0, LEFT_PANEL_WIDTH, SCREEN_HEIGHT))
        pygame.draw.rect(self.screen, PANEL_BG,
                        (SCREEN_WIDTH - RIGHT_PANEL_WIDTH, 0, RIGHT_PANEL_WIDTH, SCREEN_HEIGHT))

        # Draw play area border
        pygame.draw.rect(self.screen, DARK_GRAY,
                        (PLAY_AREA_X, 0, PLAY_AREA_WIDTH, SCREEN_HEIGHT), 1)

        # Draw sprites
        self.all_sprites.draw(self.screen)

        # Flash player when invincible
        if self.player.invincible > 0 and (self.player.invincible // 5) % 2:
            pass  # Skip drawing to create flash effect
        else:
            self.screen.blit(self.player.image, self.player.rect)

        # Draw health bar
        self.health_bar.draw(self.screen, self.health, PLAYER_MAX_HEALTH)

        # Draw score (top left of play area)
        score_text = self.font_score.render(f"${self.score}", True, GREEN)
        self.screen.blit(score_text, (PLAY_AREA_X + 10, 10))

        # Draw touch controls
        if not self.game_over:
            self.touch_controls.draw(self.screen)

        # Draw FPS
        if self.show_fps:
            fps = int(self.clock.get_fps())
            color = GREEN if fps >= 55 else YELLOW if fps >= 30 else RED
            fps_text = self.font.render(f"FPS: {fps}", True, color)
            self.screen.blit(fps_text, (PLAY_AREA_X + PLAY_AREA_WIDTH - fps_text.get_width() - 10, 10))

        # Draw pause menu
        if self.paused:
            self.pause_menu.draw(self.screen)

        # Draw game over
        if self.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            self.screen.blit(overlay, (0, 0))

            text = self.font_large.render("DELIVERY FAILED", True, RED)
            self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2,
                                    SCREEN_HEIGHT // 2 - 60))

            final_score = self.font_score.render(f"Final Score: ${self.score}", True, WHITE)
            self.screen.blit(final_score, (SCREEN_WIDTH // 2 - final_score.get_width() // 2,
                                           SCREEN_HEIGHT // 2))

            restart_text = self.font.render("Press R or tap to restart", True, WHITE)
            self.screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2,
                                            SCREEN_HEIGHT // 2 + 40))

        pygame.display.flip()

    def run(self):
        """Main game loop."""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_p:
                        if self.paused:
                            self.paused = False
                        elif not self.game_over:
                            self.toggle_pause()
                    elif event.key == pygame.K_r and self.game_over:
                        self.reset()
                    elif event.key == pygame.K_f:
                        self.show_fps = not self.show_fps

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = event.pos

                    if self.paused:
                        action = self.pause_menu.handle_click(pos)
                        if action == 'resume':
                            self.paused = False
                        elif action == 'quit':
                            running = False

                    elif self.game_over:
                        self.reset()

                    elif self.touch_controls.check_pause_tap(pos):
                        self.toggle_pause()

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
