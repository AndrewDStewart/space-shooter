"""
Space Delivery - A delivery game where you navigate obstacles to complete deliveries.

Controls:
    Keyboard:
        Left/Right Arrow Keys: Move ship
        Space: Shoot
        P or ESC: Pause game
        R: Retry level (after game over)
        Enter/Space: Proceed through menus
        F: Toggle FPS display

    Touch/Mouse:
        Pause button (right panel): Pause game
        Menu buttons: Navigate menus

Game Flow:
    Main Menu -> Level Select -> Play Level -> Level Complete/Game Over -> Level Select
"""

import asyncio
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
LEFT_PANEL_WIDTH = 80   # 10% for health + ammo bars
RIGHT_PANEL_WIDTH = 80  # 10% for pause button, progress, controls
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
CYAN = (0, 255, 255)
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
STARTING_AMMO = 30

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

# Invincibility after hit (frames)
INVINCIBILITY_FRAMES = 60

# Level progression
LEVEL_DURATION = 7200  # 2 minutes at 60 FPS


# --- Game State ---

class GameState:
    """Game state constants."""
    MENU = "menu"
    LEVEL_SELECT = "level_select"
    PLAYING = "playing"
    LEVEL_COMPLETE = "level_complete"
    GAME_OVER = "game_over"


# Level definitions
LEVELS = {
    "1-1": {"name": "Training Run", "duration": 7200, "asteroid_rate": 80, "obstacle_rate": 240},
    "1-2": {"name": "Light Traffic", "duration": 7200, "asteroid_rate": 70, "obstacle_rate": 200},
    "1-3": {"name": "Busy Route", "duration": 7200, "asteroid_rate": 60, "obstacle_rate": 180},
    "1-4": {"name": "Danger Zone", "duration": 7200, "asteroid_rate": 50, "obstacle_rate": 150},
    "1-5": {"name": "Gauntlet", "duration": 7200, "asteroid_rate": 40, "obstacle_rate": 120},
}

LEVEL_ORDER = ["1-1", "1-2", "1-3", "1-4", "1-5"]


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


class AmmoBar:
    """Vertical ammo bar display."""

    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.border_width = 2
        self.font = pygame.font.Font(None, 14)

    def draw(self, surface, current_ammo, max_ammo):
        """Draw the ammo bar."""
        # Background
        pygame.draw.rect(surface, DARK_GRAY, self.rect)

        # Ammo fill (from bottom up)
        ammo_ratio = max(0, current_ammo / max_ammo) if max_ammo > 0 else 0
        fill_height = int((self.rect.height - self.border_width * 2) * ammo_ratio)
        fill_rect = pygame.Rect(
            self.rect.x + self.border_width,
            self.rect.bottom - self.border_width - fill_height,
            self.rect.width - self.border_width * 2,
            fill_height
        )

        # Color based on ammo level
        if ammo_ratio > 0.5:
            color = CYAN
        elif ammo_ratio > 0.25:
            color = YELLOW
        else:
            color = RED

        if fill_height > 0:
            pygame.draw.rect(surface, color, fill_rect)

        # Border
        pygame.draw.rect(surface, WHITE, self.rect, self.border_width)

        # Label
        label = self.font.render("AMMO", True, WHITE)
        label_x = self.rect.x + self.rect.width // 2 - label.get_width() // 2
        surface.blit(label, (label_x, self.rect.y - label.get_height() - 1))


class ControlsList:
    """Static controls reference displayed in the right panel."""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.font_header = pygame.font.Font(None, 18)
        self.font_item = pygame.font.Font(None, 16)

    def draw(self, surface):
        """Draw the controls reference."""
        lines = [
            ("CONTROLS", self.font_header, WHITE),
            ("", None, None),
            ("\u2190\u2192  Move", self.font_item, LIGHT_GRAY),
            ("SPC Shoot", self.font_item, LIGHT_GRAY),
            (" P  Pause", self.font_item, LIGHT_GRAY),
        ]
        y = self.y
        for text, font, color in lines:
            if font is None:
                y += 4
                continue
            rendered = font.render(text, True, color)
            x = self.x + (RIGHT_PANEL_WIDTH - rendered.get_width()) // 2
            surface.blit(rendered, (x, y))
            y += rendered.get_height() + 3


class ProgressTracker:
    """Vertical progress bar showing journey to space station."""

    def __init__(self, x, y, height):
        self.x = x
        self.y = y
        self.height = height
        self.width = 20
        self.ship_size = 12
        self.station_size = 16

    def draw(self, surface, progress):
        """Draw the progress tracker with ship and station icons."""
        # Progress line (vertical)
        line_x = self.x + self.width // 2
        line_top = self.y + self.station_size + 5
        line_bottom = self.y + self.height - self.ship_size - 5

        pygame.draw.line(surface, DARK_GRAY, (line_x, line_top), (line_x, line_bottom), 2)

        # Station icon at top (destination)
        station_y = self.y + self.station_size // 2
        # Central hub
        pygame.draw.circle(surface, GRAY, (line_x, station_y), self.station_size // 2)
        pygame.draw.circle(surface, WHITE, (line_x, station_y), self.station_size // 2, 1)
        # Arms
        arm_len = self.station_size // 2 + 4
        pygame.draw.line(surface, WHITE, (line_x - arm_len, station_y), (line_x + arm_len, station_y), 2)
        pygame.draw.line(surface, WHITE, (line_x, station_y - arm_len), (line_x, station_y + arm_len), 2)

        # Mini ship icon (current progress)
        ship_y = line_bottom - int((line_bottom - line_top) * progress)
        ship_points = [
            (line_x, ship_y - self.ship_size // 2),
            (line_x - self.ship_size // 3, ship_y + self.ship_size // 2),
            (line_x + self.ship_size // 3, ship_y + self.ship_size // 2),
        ]
        pygame.draw.polygon(surface, BLUE, ship_points)
        pygame.draw.polygon(surface, WHITE, ship_points, 1)

        # Progress percentage
        percent = int(progress * 100)
        font = pygame.font.Font(None, 18)
        text = font.render(f"{percent}%", True, WHITE)
        surface.blit(text, (self.x + self.width // 2 - text.get_width() // 2, self.y + self.height + 2))


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
    """Manages on-screen touch controls (pause button only)."""

    def __init__(self):
        # Pause button (top of right panel)
        pause_size = 30
        self.pause_btn = TouchButton(
            SCREEN_WIDTH - RIGHT_PANEL_WIDTH // 2 - pause_size // 2,
            10,
            pause_size, pause_size,
            "||", GRAY
        )

    def check_pause_tap(self, pos):
        """Check if pause button was tapped."""
        return self.pause_btn.check_press(pos)

    def draw(self, surface):
        """Draw the pause button."""
        self.pause_btn.draw(surface)


class PauseMenu:
    """Pause menu overlay."""

    def __init__(self):
        self.font_large = pygame.font.Font(None, 64)
        self.font_medium = pygame.font.Font(None, 40)

        btn_width = 200
        btn_height = 50
        btn_x = SCREEN_WIDTH // 2 - btn_width // 2
        center_y = SCREEN_HEIGHT // 2

        self.resume_btn = TouchButton(btn_x, center_y - 60, btn_width, btn_height, "RESUME", GREEN)
        self.resume_btn.font = self.font_medium

        self.restart_btn = TouchButton(btn_x, center_y + 10, btn_width, btn_height, "RESTART", YELLOW)
        self.restart_btn.font = self.font_medium

        self.quit_btn = TouchButton(btn_x, center_y + 80, btn_width, btn_height, "QUIT", RED)
        self.quit_btn.font = self.font_medium

    def draw(self, surface):
        """Draw the pause menu."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        title = self.font_large.render("PAUSED", True, WHITE)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - 130))

        self.resume_btn.draw(surface)
        self.restart_btn.draw(surface)
        self.quit_btn.draw(surface)

    def handle_click(self, pos):
        """Handle click on menu."""
        if self.resume_btn.check_press(pos):
            return 'resume'
        elif self.restart_btn.check_press(pos):
            return 'restart'
        elif self.quit_btn.check_press(pos):
            return 'quit'
        return None


class LevelSelectScreen:
    """Level selection screen."""

    def __init__(self):
        self.font_title = pygame.font.Font(None, 64)
        self.font_level = pygame.font.Font(None, 36)
        self.font_name = pygame.font.Font(None, 24)
        self.font_btn = pygame.font.Font(None, 28)
        self.level_buttons = {}
        self._create_buttons()
        # Back button
        self.back_btn = pygame.Rect(20, SCREEN_HEIGHT - 50, 80, 35)

    def _create_buttons(self):
        """Create level selection buttons."""
        start_x = SCREEN_WIDTH // 2 - 150
        start_y = 120
        btn_size = 80
        gap = 20

        for i, level_id in enumerate(LEVEL_ORDER):
            row = i // 3
            col = i % 3
            x = start_x + col * (btn_size + gap)
            y = start_y + row * (btn_size + gap + 30)
            self.level_buttons[level_id] = pygame.Rect(x, y, btn_size, btn_size)

    def draw(self, surface, unlocked_levels, completed_levels):
        """Draw the level select screen."""
        surface.fill(BLACK)

        # Title
        title = self.font_title.render("WORLD 1", True, WHITE)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 40))

        # Level buttons
        for level_id, rect in self.level_buttons.items():
            level_data = LEVELS[level_id]
            is_unlocked = level_id in unlocked_levels
            is_completed = level_id in completed_levels

            # Button background
            if is_completed:
                color = DARK_GREEN
            elif is_unlocked:
                color = DARK_GRAY
            else:
                color = (40, 40, 40)

            pygame.draw.rect(surface, color, rect, border_radius=10)
            pygame.draw.rect(surface, WHITE if is_unlocked else GRAY, rect, 2, border_radius=10)

            # Level number
            level_text = self.font_level.render(level_id, True, WHITE if is_unlocked else GRAY)
            surface.blit(level_text, (rect.centerx - level_text.get_width() // 2,
                                      rect.centery - level_text.get_height() // 2 - 5))

            # Status icon
            if is_completed:
                check = self.font_name.render("✓", True, GREEN)
                surface.blit(check, (rect.centerx - check.get_width() // 2, rect.bottom - 25))
            elif not is_unlocked:
                lock = self.font_name.render("🔒", True, GRAY)
                surface.blit(lock, (rect.centerx - lock.get_width() // 2, rect.bottom - 25))

            # Level name below button
            name_text = self.font_name.render(level_data["name"], True, WHITE if is_unlocked else GRAY)
            surface.blit(name_text, (rect.centerx - name_text.get_width() // 2, rect.bottom + 5))

        # Back button
        pygame.draw.rect(surface, DARK_GRAY, self.back_btn, border_radius=8)
        pygame.draw.rect(surface, WHITE, self.back_btn, 2, border_radius=8)
        back_text = self.font_btn.render("< Back", True, WHITE)
        surface.blit(back_text, (self.back_btn.centerx - back_text.get_width() // 2,
                                 self.back_btn.centery - back_text.get_height() // 2))

    def handle_click(self, pos, unlocked_levels):
        """Handle click on level select. Returns level_id, 'back', or None."""
        if self.back_btn.collidepoint(pos):
            return 'back'
        for level_id, rect in self.level_buttons.items():
            if rect.collidepoint(pos) and level_id in unlocked_levels:
                return level_id
        return None


class LevelCompleteScreen:
    """Level completion screen."""

    def __init__(self):
        self.font_title = pygame.font.Font(None, 56)
        self.font_level = pygame.font.Font(None, 36)
        self.font_score = pygame.font.Font(None, 32)
        self.font_btn = pygame.font.Font(None, 28)

        # Buttons
        btn_width = 150
        btn_height = 45
        btn_y = SCREEN_HEIGHT - 100
        gap = 20

        self.next_btn = pygame.Rect(SCREEN_WIDTH // 2 - btn_width - gap // 2, btn_y, btn_width, btn_height)
        self.select_btn = pygame.Rect(SCREEN_WIDTH // 2 + gap // 2, btn_y, btn_width, btn_height)

    def draw(self, surface, level_id, base_score, health_bonus, has_next_level):
        """Draw the level complete screen."""
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))

        level_data = LEVELS.get(level_id, {"name": "Unknown"})
        total = base_score + health_bonus

        # Title
        title = self.font_title.render("DELIVERY COMPLETE!", True, GREEN)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 60))

        # Level info
        level_text = self.font_level.render(f"Level {level_id}: {level_data['name']}", True, WHITE)
        surface.blit(level_text, (SCREEN_WIDTH // 2 - level_text.get_width() // 2, 130))

        # Score breakdown
        y_start = 180
        line_height = 35

        pay_text = self.font_score.render(f"Delivery Pay:  ${base_score}", True, WHITE)
        surface.blit(pay_text, (SCREEN_WIDTH // 2 - pay_text.get_width() // 2, y_start))

        bonus_text = self.font_score.render(f"Health Bonus:  ${health_bonus}", True, YELLOW)
        surface.blit(bonus_text, (SCREEN_WIDTH // 2 - bonus_text.get_width() // 2, y_start + line_height))

        # Divider line
        line_y = y_start + line_height * 2
        line_width = 200
        pygame.draw.line(surface, WHITE,
                        (SCREEN_WIDTH // 2 - line_width // 2, line_y),
                        (SCREEN_WIDTH // 2 + line_width // 2, line_y), 2)

        total_text = self.font_score.render(f"Total:         ${total}", True, GREEN)
        surface.blit(total_text, (SCREEN_WIDTH // 2 - total_text.get_width() // 2, line_y + 15))

        # Buttons
        if has_next_level:
            pygame.draw.rect(surface, DARK_GREEN, self.next_btn, border_radius=8)
            pygame.draw.rect(surface, WHITE, self.next_btn, 2, border_radius=8)
            next_text = self.font_btn.render("NEXT LEVEL", True, WHITE)
            surface.blit(next_text, (self.next_btn.centerx - next_text.get_width() // 2,
                                     self.next_btn.centery - next_text.get_height() // 2))

        pygame.draw.rect(surface, DARK_GRAY, self.select_btn, border_radius=8)
        pygame.draw.rect(surface, WHITE, self.select_btn, 2, border_radius=8)
        select_text = self.font_btn.render("LEVEL SELECT", True, WHITE)
        surface.blit(select_text, (self.select_btn.centerx - select_text.get_width() // 2,
                                   self.select_btn.centery - select_text.get_height() // 2))

    def handle_click(self, pos, has_next_level):
        """Handle click. Returns 'next', 'select', or None."""
        if has_next_level and self.next_btn.collidepoint(pos):
            return 'next'
        if self.select_btn.collidepoint(pos):
            return 'select'
        return None


class MenuScreen:
    """Simple title/menu screen."""

    def __init__(self):
        self.font_title = pygame.font.Font(None, 72)
        self.font_subtitle = pygame.font.Font(None, 36)
        self.font_btn = pygame.font.Font(None, 40)

        btn_width = 200
        btn_height = 60
        self.start_btn = pygame.Rect(SCREEN_WIDTH // 2 - btn_width // 2,
                                     SCREEN_HEIGHT // 2 + 40,
                                     btn_width, btn_height)

    def draw(self, surface):
        """Draw the menu screen."""
        surface.fill(BLACK)

        # Title
        title = self.font_title.render("SPACE DELIVERY", True, BLUE)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 100))

        # Subtitle
        subtitle = self.font_subtitle.render("Navigate the asteroid field!", True, WHITE)
        surface.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 180))

        # Start button
        pygame.draw.rect(surface, DARK_GREEN, self.start_btn, border_radius=10)
        pygame.draw.rect(surface, WHITE, self.start_btn, 3, border_radius=10)
        btn_text = self.font_btn.render("START", True, WHITE)
        surface.blit(btn_text, (self.start_btn.centerx - btn_text.get_width() // 2,
                                self.start_btn.centery - btn_text.get_height() // 2))

    def handle_click(self, pos):
        """Handle click. Returns True if start button clicked."""
        return self.start_btn.collidepoint(pos)


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


class SpaceStation(pygame.sprite.Sprite):
    """Space station - destination for level completion."""

    def __init__(self):
        super().__init__()
        self.width = 200
        self.height = 150
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self._draw_station()
        self.rect = self.image.get_rect()
        # Spawn centered at top of play area
        self.rect.centerx = PLAY_AREA_X + PLAY_AREA_WIDTH // 2
        self.rect.bottom = 0
        self.speed = 1  # Slow descent

    def _draw_station(self):
        """Draw a space station with central hub and extending arms."""
        cx, cy = self.width // 2, self.height // 2

        # Central hub (large circle)
        hub_radius = 35
        pygame.draw.circle(self.image, GRAY, (cx, cy), hub_radius)
        pygame.draw.circle(self.image, WHITE, (cx, cy), hub_radius, 3)

        # Inner hub detail
        pygame.draw.circle(self.image, DARK_GRAY, (cx, cy), hub_radius - 10)
        pygame.draw.circle(self.image, BLUE, (cx, cy), 12)
        pygame.draw.circle(self.image, WHITE, (cx, cy), 12, 2)

        # Horizontal arm
        arm_width = 160
        arm_height = 20
        arm_rect = pygame.Rect(cx - arm_width // 2, cy - arm_height // 2, arm_width, arm_height)
        pygame.draw.rect(self.image, GRAY, arm_rect)
        pygame.draw.rect(self.image, WHITE, arm_rect, 2)

        # Arm end modules
        module_size = 30
        # Left module
        left_module = pygame.Rect(cx - arm_width // 2 - 5, cy - module_size // 2, module_size, module_size)
        pygame.draw.rect(self.image, DARK_GRAY, left_module)
        pygame.draw.rect(self.image, WHITE, left_module, 2)
        # Right module
        right_module = pygame.Rect(cx + arm_width // 2 - module_size + 5, cy - module_size // 2, module_size, module_size)
        pygame.draw.rect(self.image, DARK_GRAY, right_module)
        pygame.draw.rect(self.image, WHITE, right_module, 2)

        # Vertical arm (shorter)
        vert_width = 16
        vert_height = 100
        vert_rect = pygame.Rect(cx - vert_width // 2, cy - vert_height // 2, vert_width, vert_height)
        pygame.draw.rect(self.image, GRAY, vert_rect)
        pygame.draw.rect(self.image, WHITE, vert_rect, 2)

        # Top and bottom modules
        top_module = pygame.Rect(cx - module_size // 2, cy - vert_height // 2 - module_size + 5, module_size, module_size)
        pygame.draw.rect(self.image, DARK_GRAY, top_module)
        pygame.draw.rect(self.image, WHITE, top_module, 2)

        bottom_module = pygame.Rect(cx - module_size // 2, cy + vert_height // 2 - 5, module_size, module_size)
        pygame.draw.rect(self.image, DARK_GRAY, bottom_module)
        pygame.draw.rect(self.image, WHITE, bottom_module, 2)

        # Docking port (at bottom) - where player docks
        dock_width = 40
        dock_height = 15
        dock_rect = pygame.Rect(cx - dock_width // 2, cy + vert_height // 2 + module_size - 10, dock_width, dock_height)
        pygame.draw.rect(self.image, GREEN, dock_rect)
        pygame.draw.rect(self.image, WHITE, dock_rect, 2)

        # Solar panels on arm ends
        panel_width = 25
        panel_height = 50
        # Left panels
        left_panel = pygame.Rect(cx - arm_width // 2 - panel_width - 5, cy - panel_height // 2, panel_width, panel_height)
        pygame.draw.rect(self.image, (50, 50, 150), left_panel)
        pygame.draw.rect(self.image, WHITE, left_panel, 1)
        # Right panels
        right_panel = pygame.Rect(cx + arm_width // 2 + 5, cy - panel_height // 2, panel_width, panel_height)
        pygame.draw.rect(self.image, (50, 50, 150), right_panel)
        pygame.draw.rect(self.image, WHITE, right_panel, 1)

    def update(self):
        """Move station slowly downward."""
        if self.rect.top < 50:  # Stop when partially in view
            self.rect.y += self.speed


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
        self.menu_screen = MenuScreen()
        self.level_select_screen = LevelSelectScreen()
        self.level_complete_screen = LevelCompleteScreen()

        # Health bar and ammo bar in left panel
        self.health_bar = HealthBar(10, 10, 25, SCREEN_HEIGHT - 20)
        self.ammo_bar = AmmoBar(45, 10, 25, SCREEN_HEIGHT - 20)

        # Progress tracker in right panel (below pause button)
        tracker_x = SCREEN_WIDTH - RIGHT_PANEL_WIDTH // 2 - 10
        tracker_y = 50  # Below pause button
        tracker_height = 130
        self.progress_tracker = ProgressTracker(tracker_x, tracker_y, tracker_height)

        # Controls reference list in right panel (below progress tracker)
        self.controls_list = ControlsList(SCREEN_WIDTH - RIGHT_PANEL_WIDTH, tracker_y + tracker_height + 30)

        # Ammo (persists across levels; resets to STARTING_AMMO on new game)
        self.ammo = STARTING_AMMO

        # Game state
        self.game_state = GameState.MENU
        self.current_level = None
        self.completed_levels = set()
        self.unlocked_levels = {"1-1"}

        # Playing state variables
        self.paused = False
        self.arriving = False
        self.docking = False

        self._init_playing_state()

    def _init_playing_state(self):
        """Initialize playing state variables."""
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

        self.paused = False

        # Level progression
        self.level_timer = 0
        self.arriving = False
        self.docking = False
        self.station = None

        # Level-specific spawn rates (defaults)
        self.asteroid_spawn_rate = ASTEROID_SPAWN_RATE
        self.obstacle_spawn_rate = OBSTACLE_SPAWN_RATE
        self.level_duration = LEVEL_DURATION

    def start_level(self, level_id):
        """Start a specific level."""
        self.current_level = level_id
        level_data = LEVELS[level_id]

        # Reset playing state
        self._init_playing_state()

        # Apply level-specific settings
        self.level_duration = level_data["duration"]
        self.asteroid_spawn_rate = level_data["asteroid_rate"]
        self.obstacle_spawn_rate = level_data["obstacle_rate"]

        self.game_state = GameState.PLAYING

    def get_next_level(self):
        """Get the next level after current, or None if at end."""
        if self.current_level is None:
            return None
        try:
            idx = LEVEL_ORDER.index(self.current_level)
            if idx + 1 < len(LEVEL_ORDER):
                return LEVEL_ORDER[idx + 1]
        except ValueError:
            pass
        return None

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
            self.game_state = GameState.GAME_OVER

        # Keep score from going negative
        if self.score < 0:
            self.score = 0

    def toggle_pause(self):
        """Toggle pause state."""
        if self.game_state == GameState.PLAYING:
            self.paused = not self.paused

    def update(self):
        """Update game state based on current state."""
        if self.game_state == GameState.MENU:
            self.update_menu()
        elif self.game_state == GameState.LEVEL_SELECT:
            self.update_level_select()
        elif self.game_state == GameState.PLAYING:
            self.update_playing()
        elif self.game_state == GameState.LEVEL_COMPLETE:
            self.update_level_complete()
        elif self.game_state == GameState.GAME_OVER:
            self.update_game_over()

    def update_menu(self):
        """Update menu state."""
        pass  # Menu is static, handled by events

    def update_level_select(self):
        """Update level select state."""
        pass  # Level select is static, handled by events

    def update_level_complete(self):
        """Update level complete state."""
        pass  # Level complete is static, handled by events

    def update_game_over(self):
        """Update game over state."""
        pass  # Game over is static, handled by events

    def update_playing(self):
        """Update playing state."""
        if self.paused:
            return

        keys = pygame.key.get_pressed()

        # Handle docking sequence (auto-pilot)
        if self.docking:
            # Auto-fly player toward station docking port
            target_x = self.station.rect.centerx
            # Target is inside the station's rect so collision triggers
            target_y = self.station.rect.bottom - 30

            # Move horizontally toward station center
            if abs(self.player.rect.centerx - target_x) > PLAYER_SPEED:
                if self.player.rect.centerx < target_x:
                    self.player.rect.x += PLAYER_SPEED
                else:
                    self.player.rect.x -= PLAYER_SPEED
            else:
                self.player.rect.centerx = target_x

            # Move upward toward station
            if self.player.rect.top > target_y:
                self.player.rect.y -= PLAYER_SPEED // 2

            self.player.hitbox.center = self.player.rect.center

            # Check if player reached docking position
            if self.player.rect.top <= target_y and self.player.rect.centerx == target_x:
                self.complete_level()
            return

        self.player.update(keys)

        shooting = keys[pygame.K_SPACE]
        if shooting and self.player.can_shoot() and self.ammo > 0:
            self.ammo -= 1
            bullet = self.player.shoot()
            self.bullets.add(bullet)
            self.all_sprites.add(bullet)

        self.bullets.update()
        self.asteroids.update()
        self.obstacles.update()

        # Level progression timer
        self.level_timer += 1
        progress = min(1.0, self.level_timer / self.level_duration)

        # Check if station should arrive
        if progress >= 1.0 and not self.arriving:
            self.arriving = True
            self.station = SpaceStation()
            self.all_sprites.add(self.station)
            # Clear remaining obstacles for safe docking approach
            for asteroid in self.asteroids:
                asteroid.kill()
            for obstacle in self.obstacles:
                obstacle.kill()
            # Make player invincible during approach
            self.player.invincible = 9999

        # Update station and check if fully in view for auto-docking
        if self.station:
            self.station.update()
            # Start auto-docking when station is fully in view (stopped descending)
            if self.station.rect.top >= 50 and not self.docking:
                self.docking = True

        # Only spawn obstacles before station arrives
        if not self.arriving:
            self.asteroid_timer += 1
            if self.asteroid_timer >= self.asteroid_spawn_rate:
                self.spawn_asteroid()
                self.asteroid_timer = 0

            self.obstacle_timer += 1
            if self.obstacle_timer >= self.obstacle_spawn_rate:
                self.spawn_obstacle()
                self.obstacle_timer = 0

        self.handle_collisions()

    def complete_level(self):
        """Called when player successfully completes a level."""
        self.completed_levels.add(self.current_level)

        # Unlock next level
        next_level = self.get_next_level()
        if next_level:
            self.unlocked_levels.add(next_level)

        self.game_state = GameState.LEVEL_COMPLETE

    def draw(self):
        """Draw based on current game state."""
        if self.game_state == GameState.MENU:
            self.draw_menu()
        elif self.game_state == GameState.LEVEL_SELECT:
            self.draw_level_select()
        elif self.game_state == GameState.PLAYING:
            self.draw_playing()
        elif self.game_state == GameState.LEVEL_COMPLETE:
            self.draw_playing()  # Draw game background
            self.draw_level_complete()
        elif self.game_state == GameState.GAME_OVER:
            self.draw_playing()  # Draw game background
            self.draw_game_over()

        pygame.display.flip()

    def draw_menu(self):
        """Draw menu screen."""
        self.menu_screen.draw(self.screen)

    def draw_level_select(self):
        """Draw level select screen."""
        self.level_select_screen.draw(self.screen, self.unlocked_levels, self.completed_levels)

    def draw_playing(self):
        """Draw playing state."""
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

        # Draw health and ammo bars
        self.health_bar.draw(self.screen, self.health, PLAYER_MAX_HEALTH)
        self.ammo_bar.draw(self.screen, self.ammo, STARTING_AMMO)

        # Draw score (top left of play area)
        score_text = self.font_score.render(f"${self.score}", True, GREEN)
        self.screen.blit(score_text, (PLAY_AREA_X + 10, 10))

        # Draw level indicator
        if self.current_level:
            level_text = self.font.render(f"Level {self.current_level}", True, WHITE)
            self.screen.blit(level_text, (PLAY_AREA_X + 10, 45))

        # Draw progress tracker
        progress = min(1.0, self.level_timer / self.level_duration)
        self.progress_tracker.draw(self.screen, progress)

        # Draw controls reference
        self.controls_list.draw(self.screen)

        # Draw touch controls (pause button only)
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

    def draw_level_complete(self):
        """Draw level complete overlay."""
        health_bonus = int(self.health * 10)
        has_next = self.get_next_level() is not None
        self.level_complete_screen.draw(self.screen, self.current_level, self.score, health_bonus, has_next)

    def draw_game_over(self):
        """Draw game over overlay."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        text = self.font_large.render("DELIVERY FAILED", True, RED)
        self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2,
                                SCREEN_HEIGHT // 2 - 100))

        final_score = self.font_score.render(f"Final Score: ${self.score}", True, WHITE)
        self.screen.blit(final_score, (SCREEN_WIDTH // 2 - final_score.get_width() // 2,
                                       SCREEN_HEIGHT // 2 - 40))

        # Buttons
        btn_width = 150
        btn_height = 45
        btn_y = SCREEN_HEIGHT // 2 + 20
        gap = 20

        self.retry_btn = pygame.Rect(SCREEN_WIDTH // 2 - btn_width - gap // 2, btn_y, btn_width, btn_height)
        self.select_btn_gameover = pygame.Rect(SCREEN_WIDTH // 2 + gap // 2, btn_y, btn_width, btn_height)

        pygame.draw.rect(self.screen, DARK_GREEN, self.retry_btn, border_radius=8)
        pygame.draw.rect(self.screen, WHITE, self.retry_btn, 2, border_radius=8)
        retry_text = self.font.render("RETRY", True, WHITE)
        self.screen.blit(retry_text, (self.retry_btn.centerx - retry_text.get_width() // 2,
                                      self.retry_btn.centery - retry_text.get_height() // 2))

        pygame.draw.rect(self.screen, DARK_GRAY, self.select_btn_gameover, border_radius=8)
        pygame.draw.rect(self.screen, WHITE, self.select_btn_gameover, 2, border_radius=8)
        select_text = self.font.render("LEVEL SELECT", True, WHITE)
        self.screen.blit(select_text, (self.select_btn_gameover.centerx - select_text.get_width() // 2,
                                       self.select_btn_gameover.centery - select_text.get_height() // 2))

    async def run(self):
        """Main game loop."""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    running = self.handle_keydown(event, running)

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    running = self.handle_mousedown(event, running)

            self.update()
            self.draw()
            self.clock.tick(FPS)
            await asyncio.sleep(0)

        pygame.quit()

    def handle_keydown(self, event, running):
        """Handle keyboard events based on game state."""
        # Global keys
        if event.key == pygame.K_f:
            self.show_fps = not self.show_fps
            return running

        if self.game_state == GameState.MENU:
            if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                self.game_state = GameState.LEVEL_SELECT

        elif self.game_state == GameState.LEVEL_SELECT:
            pass  # Level select only uses mouse/touch

        elif self.game_state == GameState.PLAYING:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_p:
                if self.paused:
                    self.paused = False
                else:
                    self.toggle_pause()

        elif self.game_state == GameState.LEVEL_COMPLETE:
            if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                # Go to next level
                next_level = self.get_next_level()
                if next_level:
                    self.start_level(next_level)
                else:
                    self.game_state = GameState.LEVEL_SELECT
            elif event.key == pygame.K_r:
                self.game_state = GameState.LEVEL_SELECT

        elif self.game_state == GameState.GAME_OVER:
            if event.key == pygame.K_r:
                self.start_level(self.current_level)
            elif event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                self.game_state = GameState.LEVEL_SELECT

        return running

    def handle_mousedown(self, event, running):
        """Handle mouse/touch events based on game state."""
        pos = event.pos

        if self.game_state == GameState.MENU:
            if self.menu_screen.handle_click(pos):
                self.ammo = STARTING_AMMO
                self.game_state = GameState.LEVEL_SELECT

        elif self.game_state == GameState.LEVEL_SELECT:
            result = self.level_select_screen.handle_click(pos, self.unlocked_levels)
            if result == 'back':
                self.game_state = GameState.MENU
            elif result:
                self.start_level(result)

        elif self.game_state == GameState.PLAYING:
            if self.paused:
                action = self.pause_menu.handle_click(pos)
                if action == 'resume':
                    self.paused = False
                elif action == 'restart':
                    self.start_level(self.current_level)
                elif action == 'quit':
                    self.game_state = GameState.LEVEL_SELECT
            elif self.touch_controls.check_pause_tap(pos):
                self.toggle_pause()

        elif self.game_state == GameState.LEVEL_COMPLETE:
            has_next = self.get_next_level() is not None
            action = self.level_complete_screen.handle_click(pos, has_next)
            if action == 'next':
                next_level = self.get_next_level()
                if next_level:
                    self.start_level(next_level)
            elif action == 'select':
                self.game_state = GameState.LEVEL_SELECT

        elif self.game_state == GameState.GAME_OVER:
            if hasattr(self, 'retry_btn') and self.retry_btn.collidepoint(pos):
                self.start_level(self.current_level)
            elif hasattr(self, 'select_btn_gameover') and self.select_btn_gameover.collidepoint(pos):
                self.game_state = GameState.LEVEL_SELECT

        return running


async def main():
    """Entry point."""
    game = Game()
    await game.run()


asyncio.run(main())
