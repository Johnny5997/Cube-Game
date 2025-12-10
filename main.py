import pygame
import random
import math
import json
import os

# Initialize pygame
pygame.init()
pygame.mixer.init()

# Constants
WIDTH, HEIGHT = 1000, 700
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)
GRAY = (128, 128, 128)

# Game settings
PLAYER_SIZE = 50
ENEMY_SIZE = 50
PROJECTILE_SIZE = 10
POWERUP_SIZE = 30


class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-3, 3)
        self.color = color
        self.lifetime = 30
        self.size = random.randint(3, 8)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1
        self.size = max(1, self.size - 0.2)

    def draw(self, screen):
        if self.lifetime > 0:
            alpha = int(255 * (self.lifetime / 30))
            s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (self.size, self.size), self.size)
            screen.blit(s, (int(self.x - self.size), int(self.y - self.size)))


class Projectile:
    def __init__(self, x, y, target_x, target_y):
        self.x = x
        self.y = y
        angle = math.atan2(target_y - y, target_x - x)
        self.vx = math.cos(angle) * 8
        self.vy = math.sin(angle) * 8
        self.active = True

    def update(self):
        self.x += self.vx
        self.y += self.vy
        if self.x < 0 or self.x > WIDTH or self.y < 0 or self.y > HEIGHT:
            self.active = False

    def draw(self, screen):
        pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), PROJECTILE_SIZE)


class PowerUp:
    def __init__(self, x, y, type):
        self.x = x
        self.y = y
        self.type = type  # "health", "speed", "shield"
        self.lifetime = 600  # 10 seconds at 60 FPS
        self.colors = {
            "health": GREEN,
            "speed": CYAN,
            "shield": PURPLE
        }

    def update(self):
        self.lifetime -= 1
        return self.lifetime > 0

    def draw(self, screen):
        color = self.colors[self.type]
        pulse = abs(math.sin(pygame.time.get_ticks() / 200)) * 50
        pygame.draw.circle(screen, tuple(min(255, c + pulse) for c in color),
                           (int(self.x), int(self.y)), POWERUP_SIZE)
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), POWERUP_SIZE, 2)


class Player:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.speed = 4
        self.max_stamina = 100
        self.stamina = self.max_stamina
        self.dash_cost = 30
        self.dash_speed = 12
        self.is_dashing = False
        self.dash_cooldown = 0
        self.health = 100
        self.max_health = 100
        self.shield = False
        self.shield_timer = 0
        self.speed_boost = False
        self.speed_boost_timer = 0

    def move(self, keys, dt):
        current_speed = self.speed

        # Update buffs
        if self.shield_timer > 0:
            self.shield_timer -= 1
            if self.shield_timer == 0:
                self.shield = False

        if self.speed_boost_timer > 0:
            self.speed_boost_timer -= 1
            current_speed = self.speed * 1.5
            if self.speed_boost_timer == 0:
                self.speed_boost = False

        # Dash cooldown
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1

        # Stamina regeneration
        if not self.is_dashing and self.stamina < self.max_stamina:
            self.stamina = min(self.max_stamina, self.stamina + 0.5)

        dx, dy = 0, 0
        if keys[pygame.K_w]:
            dy -= 1
        if keys[pygame.K_s]:
            dy += 1
        if keys[pygame.K_a]:
            dx -= 1
        if keys[pygame.K_d]:
            dx += 1

        # Normalize diagonal movement
        if dx != 0 and dy != 0:
            dx *= 0.707
            dy *= 0.707

        # Check for dash
        if keys[pygame.K_SPACE] and self.stamina >= self.dash_cost and self.dash_cooldown == 0 and (dx != 0 or dy != 0):
            self.is_dashing = True
            self.stamina -= self.dash_cost
            self.dash_cooldown = 20
            speed = self.dash_speed
        elif self.is_dashing:
            speed = self.dash_speed
            self.is_dashing = False
        else:
            speed = current_speed

        self.x += dx * speed
        self.y += dy * speed

        # Boundary checking
        self.x = max(PLAYER_SIZE // 2, min(WIDTH - PLAYER_SIZE // 2, self.x))
        self.y = max(PLAYER_SIZE // 2, min(HEIGHT - PLAYER_SIZE // 2, self.y))

    def shoot(self, mouse_pos):
        return Projectile(self.x, self.y, mouse_pos[0], mouse_pos[1])

    def take_damage(self, amount):
        if self.shield:
            return False
        self.health -= amount
        return self.health <= 0

    def draw(self, screen):
        # Draw shield effect
        if self.shield:
            pulse = abs(math.sin(pygame.time.get_ticks() / 100)) * 10
            pygame.draw.circle(screen, PURPLE, (int(self.x), int(self.y)),
                               PLAYER_SIZE // 2 + 10 + int(pulse), 3)

        # Draw speed boost effect
        if self.speed_boost:
            trail_color = (*CYAN, 100)
            s = pygame.Surface((PLAYER_SIZE + 10, PLAYER_SIZE + 10), pygame.SRCALPHA)
            pygame.draw.rect(s, trail_color, (0, 0, PLAYER_SIZE + 10, PLAYER_SIZE + 10))
            screen.blit(s, (int(self.x - PLAYER_SIZE // 2 - 5), int(self.y - PLAYER_SIZE // 2 - 5)))

        # Draw player
        pygame.draw.rect(screen, self.color,
                         (int(self.x - PLAYER_SIZE // 2), int(self.y - PLAYER_SIZE // 2),
                          PLAYER_SIZE, PLAYER_SIZE))
        pygame.draw.rect(screen, WHITE,
                         (int(self.x - PLAYER_SIZE // 2), int(self.y - PLAYER_SIZE // 2),
                          PLAYER_SIZE, PLAYER_SIZE), 2)


class Enemy:
    def __init__(self, x, y, difficulty):
        self.x = x
        self.y = y
        self.speed = 1 + (difficulty * 0.1)
        self.health = 2 + difficulty
        self.max_health = self.health
        self.type = random.choice(["normal", "fast", "tank"])

        if self.type == "fast":
            self.speed *= 1.5
            self.health = max(1, self.health - 1)
            self.color = ORANGE
        elif self.type == "tank":
            self.speed *= 0.7
            self.health *= 2
            self.color = (100, 100, 200)
        else:
            self.color = BLUE

    def move_towards_player(self, player_x, player_y):
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.sqrt(dx ** 2 + dy ** 2)
        if dist > 0:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

    def take_damage(self, amount):
        self.health -= amount
        return self.health <= 0

    def draw(self, screen):
        pygame.draw.rect(screen, self.color,
                         (int(self.x - ENEMY_SIZE // 2), int(self.y - ENEMY_SIZE // 2),
                          ENEMY_SIZE, ENEMY_SIZE))
        # Health bar
        bar_width = ENEMY_SIZE
        bar_height = 5
        health_width = int((self.health / self.max_health) * bar_width)
        pygame.draw.rect(screen, RED,
                         (int(self.x - ENEMY_SIZE // 2), int(self.y - ENEMY_SIZE // 2 - 10),
                          bar_width, bar_height))
        pygame.draw.rect(screen, GREEN,
                         (int(self.x - ENEMY_SIZE // 2), int(self.y - ENEMY_SIZE // 2 - 10),
                          health_width, bar_height))


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Enhanced Cube Survival")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

        # Game state
        self.state = "menu"  # menu, playing, paused, game_over, customize
        self.player_color = RED
        self.available_colors = [RED, GREEN, BLUE, YELLOW, PURPLE, ORANGE, CYAN]
        self.color_names = ["Red", "Green", "Blue", "Yellow", "Purple", "Orange", "Cyan"]
        self.selected_color_idx = 0

        self.reset_game()

        # High score
        self.high_score = self.load_high_score()

    def reset_game(self):
        self.player = Player(WIDTH // 2, HEIGHT // 2, self.player_color)
        self.enemies = []
        self.projectiles = []
        self.powerups = []
        self.particles = []
        self.score = 0
        self.wave = 1
        self.spawn_timer = 0
        self.spawn_interval = 180  # 3 seconds at 60 FPS
        self.powerup_timer = 0
        self.difficulty = 0
        self.kills = 0

    def load_high_score(self):
        if os.path.exists("high_score.txt"):
            with open("high_score.txt", "r") as f:
                return int(f.read())
        return 0

    def save_high_score(self):
        with open("high_score.txt", "w") as f:
            f.write(str(self.high_score))

    def spawn_enemy(self):
        side = random.choice(["top", "bottom", "left", "right"])
        if side == "top":
            x, y = random.randint(0, WIDTH), -ENEMY_SIZE
        elif side == "bottom":
            x, y = random.randint(0, WIDTH), HEIGHT + ENEMY_SIZE
        elif side == "left":
            x, y = -ENEMY_SIZE, random.randint(0, HEIGHT)
        else:
            x, y = WIDTH + ENEMY_SIZE, random.randint(0, HEIGHT)

        self.enemies.append(Enemy(x, y, self.difficulty))

    def spawn_powerup(self):
        x = random.randint(50, WIDTH - 50)
        y = random.randint(50, HEIGHT - 50)
        type = random.choice(["health", "speed", "shield"])
        self.powerups.append(PowerUp(x, y, type))

    def handle_menu(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.state = "playing"
                    self.reset_game()
                elif event.key == pygame.K_c:
                    self.state = "customize"

    def handle_customize(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.selected_color_idx = (self.selected_color_idx - 1) % len(self.available_colors)
                elif event.key == pygame.K_RIGHT:
                    self.selected_color_idx = (self.selected_color_idx + 1) % len(self.available_colors)
                elif event.key == pygame.K_RETURN:
                    self.player_color = self.available_colors[self.selected_color_idx]
                    self.state = "menu"
                elif event.key == pygame.K_ESCAPE:
                    self.state = "menu"

    def handle_playing(self, events, keys):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = "paused"
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self.projectiles.append(self.player.shoot(pygame.mouse.get_pos()))

        dt = self.clock.get_time() / 1000.0
        self.player.move(keys, dt)

        # Spawn enemies
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_interval:
            enemies_to_spawn = 1 + (self.wave // 3)
            for _ in range(enemies_to_spawn):
                self.spawn_enemy()
            self.spawn_timer = 0
            self.wave += 1
            self.difficulty += 1

        # Spawn powerups
        self.powerup_timer += 1
        if self.powerup_timer >= 600:  # Every 10 seconds
            self.spawn_powerup()
            self.powerup_timer = 0

        # Update enemies
        for enemy in self.enemies[:]:
            enemy.move_towards_player(self.player.x, self.player.y)

            # Check collision with player
            dx = self.player.x - enemy.x
            dy = self.player.y - enemy.y
            dist = math.sqrt(dx ** 2 + dy ** 2)
            if dist < (PLAYER_SIZE + ENEMY_SIZE) / 2:
                if self.player.take_damage(10):
                    self.state = "game_over"
                    if self.score > self.high_score:
                        self.high_score = self.score
                        self.save_high_score()
                self.enemies.remove(enemy)
                for _ in range(20):
                    self.particles.append(Particle(enemy.x, enemy.y, enemy.color))

        # Update projectiles
        for proj in self.projectiles[:]:
            proj.update()
            if not proj.active:
                self.projectiles.remove(proj)
                continue

            # Check collision with enemies
            for enemy in self.enemies[:]:
                dx = proj.x - enemy.x
                dy = proj.y - enemy.y
                dist = math.sqrt(dx ** 2 + dy ** 2)
                if dist < (PROJECTILE_SIZE + ENEMY_SIZE / 2):
                    if enemy.take_damage(1):
                        self.enemies.remove(enemy)
                        self.score += 10
                        self.kills += 1
                        for _ in range(15):
                            self.particles.append(Particle(enemy.x, enemy.y, enemy.color))
                    self.projectiles.remove(proj)
                    break

        # Update powerups
        for powerup in self.powerups[:]:
            if not powerup.update():
                self.powerups.remove(powerup)
                continue

            # Check collision with player
            dx = self.player.x - powerup.x
            dy = self.player.y - powerup.y
            dist = math.sqrt(dx ** 2 + dy ** 2)
            if dist < (PLAYER_SIZE + POWERUP_SIZE) / 2:
                if powerup.type == "health":
                    self.player.health = min(self.player.max_health, self.player.health + 30)
                elif powerup.type == "speed":
                    self.player.speed_boost = True
                    self.player.speed_boost_timer = 300
                elif powerup.type == "shield":
                    self.player.shield = True
                    self.player.shield_timer = 300
                self.powerups.remove(powerup)
                for _ in range(10):
                    self.particles.append(Particle(powerup.x, powerup.y, powerup.colors[powerup.type]))

        # Update particles
        for particle in self.particles[:]:
            particle.update()
            if particle.lifetime <= 0:
                self.particles.remove(particle)

        # Increase score over time
        self.score += 0.1

    def handle_paused(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = "playing"
                elif event.key == pygame.K_q:
                    self.state = "menu"

    def handle_game_over(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.state = "playing"
                    self.reset_game()
                elif event.key == pygame.K_ESCAPE:
                    self.state = "menu"

    def draw_menu(self):
        self.screen.fill(BLACK)

        title = self.font.render("ENHANCED CUBE SURVIVAL", True, YELLOW)
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 150))

        instructions = [
            "Press ENTER to Start",
            "Press C to Customize",
            "",
            "Controls:",
            "WASD - Move",
            "SPACE - Dash (uses stamina)",
            "Left Click - Shoot",
            "ESC - Pause",
        ]

        y = 250
        for line in instructions:
            text = self.small_font.render(line, True, WHITE)
            self.screen.blit(text, (WIDTH // 2 - text.get_width() // 2, y))
            y += 35

        high_score_text = self.font.render(f"High Score: {int(self.high_score)}", True, GREEN)
        self.screen.blit(high_score_text, (WIDTH // 2 - high_score_text.get_width() // 2, HEIGHT - 80))

    def draw_customize(self):
        self.screen.fill(BLACK)

        title = self.font.render("CUSTOMIZE YOUR CUBE", True, YELLOW)
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 150))

        # Draw color options
        y = 300
        for i, (color, name) in enumerate(zip(self.available_colors, self.color_names)):
            x = WIDTH // 2 - 100
            if i == self.selected_color_idx:
                pygame.draw.rect(self.screen, WHITE, (x - 10, y - 10, 220, 70), 3)

            pygame.draw.rect(self.screen, color, (x, y, 50, 50))
            text = self.small_font.render(name, True, WHITE)
            self.screen.blit(text, (x + 70, y + 15))
            y += 80

        instructions = self.small_font.render("Use LEFT/RIGHT arrows, ENTER to confirm, ESC to go back", True, GRAY)
        self.screen.blit(instructions, (WIDTH // 2 - instructions.get_width() // 2, HEIGHT - 100))

    def draw_playing(self, fps):
        self.screen.fill(BLACK)

        # Draw particles
        for particle in self.particles:
            particle.draw(self.screen)

        # Draw powerups
        for powerup in self.powerups:
            powerup.draw(self.screen)

        # Draw enemies
        for enemy in self.enemies:
            enemy.draw(self.screen)

        # Draw projectiles
        for proj in self.projectiles:
            proj.draw(self.screen)

        # Draw player
        self.player.draw(self.screen)

        # Draw UI
        # FPS Counter
        fps_text = self.small_font.render(f"FPS: {int(fps)}", True, WHITE)
        self.screen.blit(fps_text, (WIDTH - 100, 10))

        # Score
        score_text = self.font.render(f"Score: {int(self.score)}", True, WHITE)
        self.screen.blit(score_text, (10, 10))

        # Wave
        wave_text = self.small_font.render(f"Wave: {self.wave}", True, CYAN)
        self.screen.blit(wave_text, (10, 50))

        # Kills
        kills_text = self.small_font.render(f"Kills: {self.kills}", True, RED)
        self.screen.blit(kills_text, (10, 80))

        # Health bar
        bar_width = 200
        bar_height = 20
        health_width = int((self.player.health / self.player.max_health) * bar_width)
        pygame.draw.rect(self.screen, GRAY, (10, HEIGHT - 70, bar_width, bar_height))
        pygame.draw.rect(self.screen, RED, (10, HEIGHT - 70, health_width, bar_height))
        pygame.draw.rect(self.screen, WHITE, (10, HEIGHT - 70, bar_width, bar_height), 2)
        health_text = self.small_font.render(f"Health: {int(self.player.health)}", True, WHITE)
        self.screen.blit(health_text, (10, HEIGHT - 95))

        # Stamina bar
        stamina_width = int((self.player.stamina / self.player.max_stamina) * bar_width)
        pygame.draw.rect(self.screen, GRAY, (10, HEIGHT - 40, bar_width, bar_height))
        pygame.draw.rect(self.screen, GREEN, (10, HEIGHT - 40, stamina_width, bar_height))
        pygame.draw.rect(self.screen, WHITE, (10, HEIGHT - 40, bar_width, bar_height), 2)
        stamina_text = self.small_font.render(f"Stamina", True, WHITE)
        self.screen.blit(stamina_text, (10, HEIGHT - 20))

        # Active buffs
        buff_y = HEIGHT - 70
        if self.player.shield:
            shield_text = self.small_font.render("SHIELD ACTIVE", True, PURPLE)
            self.screen.blit(shield_text, (WIDTH - 200, buff_y))
            buff_y -= 30
        if self.player.speed_boost:
            speed_text = self.small_font.render("SPEED BOOST", True, CYAN)
            self.screen.blit(speed_text, (WIDTH - 200, buff_y))

    def draw_paused(self):
        # Draw game in background
        for enemy in self.enemies:
            enemy.draw(self.screen)
        for proj in self.projectiles:
            proj.draw(self.screen)
        self.player.draw(self.screen)

        # Draw pause overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        title = self.font.render("PAUSED", True, YELLOW)
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 100))

        resume = self.small_font.render("Press ESC to Resume", True, WHITE)
        self.screen.blit(resume, (WIDTH // 2 - resume.get_width() // 2, HEIGHT // 2))

        quit_text = self.small_font.render("Press Q to Quit to Menu", True, WHITE)
        self.screen.blit(quit_text, (WIDTH // 2 - quit_text.get_width() // 2, HEIGHT // 2 + 40))

    def draw_game_over(self):
        self.screen.fill(BLACK)

        title = self.font.render("GAME OVER", True, RED)
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 200))

        score_text = self.font.render(f"Final Score: {int(self.score)}", True, WHITE)
        self.screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, 280))

        kills_text = self.font.render(f"Enemies Killed: {self.kills}", True, WHITE)
        self.screen.blit(kills_text, (WIDTH // 2 - kills_text.get_width() // 2, 330))

        wave_text = self.font.render(f"Waves Survived: {self.wave - 1}", True, WHITE)
        self.screen.blit(wave_text, (WIDTH // 2 - wave_text.get_width() // 2, 380))

        if self.score >= self.high_score:
            new_high = self.font.render("NEW HIGH SCORE!", True, YELLOW)
            self.screen.blit(new_high, (WIDTH // 2 - new_high.get_width() // 2, 430))

        restart = self.small_font.render("Press SPACE to Restart", True, GREEN)
        self.screen.blit(restart, (WIDTH // 2 - restart.get_width() // 2, HEIGHT - 150))

        menu_text = self.small_font.render("Press ESC for Menu", True, WHITE)
        self.screen.blit(menu_text, (WIDTH // 2 - menu_text.get_width() // 2, HEIGHT - 100))

    def run(self):
        running = True
        while running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    running = False

            keys = pygame.key.get_pressed()

            if self.state == "menu":
                self.handle_menu(events)
                self.draw_menu()
            elif self.state == "customize":
                self.handle_customize(events)
                self.draw_customize()
            elif self.state == "playing":
                self.handle_playing(events, keys)
                self.draw_playing(self.clock.get_fps())
            elif self.state == "paused":
                self.handle_paused(events)
                self.draw_paused()
            elif self.state == "game_over":
                self.handle_game_over(events)
                self.draw_game_over()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()