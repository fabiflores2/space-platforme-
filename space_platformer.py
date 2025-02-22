import pygame
import random
import os
import math

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# Create the game window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Space Platformer")
clock = pygame.time.Clock()

# Global game instance
game_instance = None

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.current_color = color
        self.font = pygame.font.Font(None, 36)
        self.is_hovered = False
        
    def draw(self, surface):
        # Update color based on hover state
        mouse_pos = pygame.mouse.get_pos()
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        self.current_color = self.hover_color if self.is_hovered else self.color
        
        # Draw button
        pygame.draw.rect(surface, self.current_color, self.rect)
        pygame.draw.rect(surface, WHITE, self.rect, 2)  # Border
        
        # Draw text
        text_surface = self.font.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.is_hovered:
                return True
        return False

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.original_image = pygame.Surface((24, 32), pygame.SRCALPHA)
        pygame.draw.circle(self.original_image, WHITE, (12, 10), 10)
        pygame.draw.rect(self.original_image, WHITE, (6, 10, 12, 20))
        pygame.draw.rect(self.original_image, (100, 200, 255), (8, 7, 8, 6))
        pygame.draw.rect(self.original_image, WHITE, (2, 12, 4, 12))
        
        self.image = self.original_image
        self.rect = self.image.get_rect()
        self.reset_position()
        self.velocity_x = 0
        self.velocity_y = 0
        self.jumping = False
        self.facing_right = True

    def reset_position(self):
        self.rect.centerx = SCREEN_WIDTH // 4
        self.rect.bottom = SCREEN_HEIGHT - 100
        self.velocity_x = 0
        self.velocity_y = 0
        self.jumping = False
    
    def update(self):
        # Apply gravity
        self.velocity_y += 0.5
        if self.velocity_y > 15:
            self.velocity_y = 15
        
        # Apply friction
        self.velocity_x *= 0.9
        
        # Move horizontally
        self.rect.x += self.velocity_x
        
        # Keep in bounds
        if self.rect.left < 0:
            self.rect.left = 0
            self.velocity_x = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
            self.velocity_x = 0
        
        # Move vertically
        self.rect.y += self.velocity_y
        
        # Handle keyboard input
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.velocity_x = max(self.velocity_x - 1, -6)
            if self.facing_right:
                self.facing_right = False
                self.image = pygame.transform.flip(self.original_image, True, False)
        if keys[pygame.K_RIGHT]:
            self.velocity_x = min(self.velocity_x + 1, 6)
            if not self.facing_right:
                self.facing_right = True
                self.image = self.original_image

    def jump(self):
        if not self.jumping:
            self.velocity_y = -15
            self.jumping = True

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width):
        super().__init__()
        self.image = pygame.Surface((width, 30), pygame.SRCALPHA)  
        pygame.draw.ellipse(self.image, (100, 100, 100), (0, 0, width, 30))
        for _ in range(3):
            crater_x = random.randint(5, width-10)
            pygame.draw.circle(self.image, (80, 80, 80), (crater_x, 15), 3)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.moving = False
        self.speed = 0
        self.distance = 0
        self.original_x = x
        self.moved = 0
        self.vanishing = False
        self.time = 0
        self.visible_time = 0
        self.visible = True

class Star(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        points = []
        for i in range(5):
            angle = i * (2 * math.pi / 5) - math.pi / 2
            points.append((10 + 10 * math.cos(angle),
                         10 + 10 * math.sin(angle)))
            angle += math.pi / 5
            points.append((10 + 4 * math.cos(angle),
                         10 + 4 * math.sin(angle)))
        pygame.draw.polygon(self.image, YELLOW, points)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.original_y = y
        self.angle = random.random() * 6.28
        
    def update(self):
        self.angle += 0.05
        self.rect.y = self.original_y + math.sin(self.angle) * 5

class Game:
    def __init__(self):
        global game_instance
        game_instance = self
        self.reset_game()
        self.state = "MENU"
        self.max_levels = 6
        self.lives = 3
        
        self.background_stars = []
        for _ in range(100):
            self.background_stars.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'size': random.randint(1, 3),
                'brightness': random.randint(100, 255)
            })
        
        button_width = 200
        button_height = 50
        center_x = SCREEN_WIDTH // 2 - button_width // 2
        
        self.start_button = Button(center_x, 250, button_width, button_height,
                                 "Iniciar Juego", GREEN, (0, 200, 0))
        self.restart_button = Button(center_x, 320, button_width, button_height,
                                   "Reiniciar", BLUE, (0, 0, 200))
        self.resume_button = Button(center_x, 250, button_width, button_height,
                                  "Continuar", GREEN, (0, 200, 0))
        self.menu_button = Button(center_x, 320, button_width, button_height,
                                "Menú Principal", BLUE, (0, 0, 200))
    
    def reset_game(self):
        self.score = 0
        self.level = 1
        self.lives = 3
        self.reset_level()
    
    def reset_level(self):
        self.all_sprites = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()
        self.stars = pygame.sprite.Group()
        
        self.player = Player()
        self.all_sprites.add(self.player)
        
        if self.level == 1:
            self.create_level_1()
        elif self.level == 2:
            self.create_level_2()
        elif self.level == 3:
            self.create_level_3()
        elif self.level == 4:
            self.create_level_4()
        elif self.level == 5:
            self.create_level_5()
        elif self.level == 6:
            self.create_level_6()
    
    def lose_life(self):
        self.lives -= 1
        print(f"Vidas restantes: {self.lives}")  
        if self.lives > 0:
            self.player.reset_position()
            self.reset_level()
        else:
            self.state = "GAME_OVER"
    
    def update(self):
        if self.state == "PLAYING":
            self.all_sprites.update()
            
            hits = pygame.sprite.spritecollide(self.player, self.platforms, False)
            if hits and self.player.velocity_y > 0:
                lowest = hits[0]
                for hit in hits:
                    if hit.rect.bottom > lowest.rect.bottom:
                        lowest = hit
                
                if self.player.rect.bottom < lowest.rect.centery + 15:
                    self.player.rect.bottom = lowest.rect.top
                    self.player.velocity_y = 0
                    self.player.jumping = False
            
            if self.player.rect.top > SCREEN_HEIGHT:
                print("¡Jugador cayó!")  
                self.lose_life()
                return
            
            for platform in self.platforms:
                if hasattr(platform, 'moving') and platform.moving:
                    platform.moved += platform.speed
                    if abs(platform.moved) > platform.distance:
                        platform.speed *= -1
                    platform.rect.x = platform.original_x + platform.moved
                
                if hasattr(platform, 'vanishing') and platform.vanishing:
                    if platform.visible and self.player.rect.bottom == platform.rect.top:
                        platform.visible_time -= 1/FPS
                        if platform.visible_time <= 0:
                            platform.visible = False
                            platform.rect.y = SCREEN_HEIGHT + 100
            
            star_hits = pygame.sprite.spritecollide(self.player, self.stars, True)
            for star in star_hits:
                self.score += 10
            
            if len(self.stars) == 0:
                if self.level < self.max_levels:
                    self.level += 1
                    self.reset_level()
                else:
                    self.state = "GAME_OVER"

    def create_level_1(self):
        platforms_data = [
            {"x": 50, "y": SCREEN_HEIGHT - 100, "width": 300},
            {"x": 350, "y": SCREEN_HEIGHT - 180, "width": 300},
            {"x": 100, "y": SCREEN_HEIGHT - 260, "width": 300},
            {"x": 400, "y": SCREEN_HEIGHT - 340, "width": 300},
            {"x": 200, "y": SCREEN_HEIGHT - 420, "width": 300},
        ]
        self.create_platforms(platforms_data)
    
    def create_level_2(self):
        platforms_data = [
            {"x": 50, "y": SCREEN_HEIGHT - 100, "width": 250},
            {"x": 400, "y": SCREEN_HEIGHT - 180, "width": 250},
            {"x": 50, "y": SCREEN_HEIGHT - 260, "width": 250},
            {"x": 400, "y": SCREEN_HEIGHT - 340, "width": 250},
            {"x": 50, "y": SCREEN_HEIGHT - 420, "width": 250},
            {"x": 400, "y": SCREEN_HEIGHT - 500, "width": 250},
        ]
        self.create_platforms(platforms_data)
    
    def create_level_3(self):
        platforms_data = [
            {"x": 50, "y": SCREEN_HEIGHT - 100, "width": 200},
            {"x": 350, "y": SCREEN_HEIGHT - 200, "width": 200},
            {"x": 650, "y": SCREEN_HEIGHT - 300, "width": 200},
            {"x": 350, "y": SCREEN_HEIGHT - 400, "width": 200},
            {"x": 50, "y": SCREEN_HEIGHT - 500, "width": 200},
            {"x": 350, "y": SCREEN_HEIGHT - 500, "width": 200},
        ]
        self.create_platforms(platforms_data)
    
    def create_level_4(self):
        platforms_data = [
            {"x": 50, "y": SCREEN_HEIGHT - 100, "width": 200},  
            {"x": 300, "y": SCREEN_HEIGHT - 200, "width": 150, "moving": True, "speed": 2, "distance": 200},
            {"x": 550, "y": SCREEN_HEIGHT - 300, "width": 150, "moving": True, "speed": -2, "distance": 200},
            {"x": 300, "y": SCREEN_HEIGHT - 400, "width": 150, "moving": True, "speed": 2, "distance": 200},
            {"x": 50, "y": SCREEN_HEIGHT - 500, "width": 200},  
        ]
        self.create_platforms(platforms_data)
    
    def create_level_5(self):
        platforms_data = [
            {"x": 50, "y": SCREEN_HEIGHT - 100, "width": 200},  
            {"x": 300, "y": SCREEN_HEIGHT - 200, "width": 180, "vanishing": True, "time": 3},  
            {"x": 550, "y": SCREEN_HEIGHT - 300, "width": 180, "vanishing": True, "time": 3},
            {"x": 300, "y": SCREEN_HEIGHT - 400, "width": 180, "vanishing": True, "time": 3},
            {"x": 50, "y": SCREEN_HEIGHT - 500, "width": 200},  
            {"x": 300, "y": SCREEN_HEIGHT - 500, "width": 200},  
        ]
        self.create_platforms(platforms_data)
    
    def create_level_6(self):
        platforms_data = [
            {"x": 50, "y": SCREEN_HEIGHT - 100, "width": 200},  
            {"x": 300, "y": SCREEN_HEIGHT - 200, "width": 150, "moving": True, "speed": 2, "distance": 200},
            {"x": 550, "y": SCREEN_HEIGHT - 300, "width": 150, "vanishing": True, "time": 2.5},
            {"x": 300, "y": SCREEN_HEIGHT - 400, "width": 150, "moving": True, "speed": -2, "distance": 200},
            {"x": 550, "y": SCREEN_HEIGHT - 500, "width": 150, "vanishing": True, "time": 2.5},
            {"x": 50, "y": SCREEN_HEIGHT - 500, "width": 200},  
        ]
        self.create_platforms(platforms_data)

    def create_platforms(self, platforms_data):
        for data in platforms_data:
            platform = Platform(data["x"], data["y"], data["width"])
            
            if "moving" in data:
                platform.moving = True
                platform.speed = data["speed"]
                platform.distance = data["distance"]
                platform.original_x = data["x"]
                platform.moved = 0
            else:
                platform.moving = False
            
            if "vanishing" in data:
                platform.vanishing = True
                platform.time = data["time"]
                platform.visible_time = data["time"]
                platform.visible = True
            else:
                platform.vanishing = False
            
            self.platforms.add(platform)
            self.all_sprites.add(platform)
            
            star = Star(data["x"] + data["width"]//2, data["y"] - 30)
            self.stars.add(star)
            self.all_sprites.add(star)
        
        self.total_stars = len(self.stars)

    def draw(self):
        screen.fill(BLACK)  
        
        for star in self.background_stars:
            brightness = star['brightness']
            color = (brightness, brightness, brightness)
            pygame.draw.circle(screen, color, (star['x'], star['y']), star['size'])
            
            star['brightness'] = max(100, min(255, star['brightness'] + random.randint(-5, 5)))
        
        if self.state == "MENU":
            font = pygame.font.Font(None, 74)
            for i in range(3):
                title_glow = font.render("Space Platformer", True, (0, 0, 50 + i * 30))
                title_rect = title_glow.get_rect(center=(SCREEN_WIDTH/2 + random.randint(-1, 1), 150 + random.randint(-1, 1)))
                screen.blit(title_glow, title_rect)
            
            title = font.render("Space Platformer", True, WHITE)
            title_rect = title.get_rect(center=(SCREEN_WIDTH/2, 150))
            screen.blit(title, title_rect)
            
            self.start_button.draw(screen)
            
        elif self.state == "PLAYING":
            self.all_sprites.draw(screen)
            
            font = pygame.font.Font(None, 36)
            score_text = font.render(f'Score: {self.score}', True, WHITE)
            level_text = font.render(f'Level: {self.level}', True, WHITE)
            stars_text = font.render(f'Stars: {self.total_stars - len(self.stars)}/{self.total_stars}', True, YELLOW)
            lives_text = font.render(f'Vidas: {self.lives}', True, RED)  
            
            screen.blit(score_text, (10, 10))
            screen.blit(level_text, (10, 40))
            screen.blit(stars_text, (10, 70))
            screen.blit(lives_text, (10, 100))  
            
            heart_size = 20
            for i in range(self.lives):
                heart_x = SCREEN_WIDTH - 30 - (i * (heart_size + 10))
                heart_y = 20
                points = [
                    (heart_x, heart_y + 6),
                    (heart_x - 6, heart_y),
                    (heart_x - 6, heart_y - 6),
                    (heart_x, heart_y - 12),
                    (heart_x + 6, heart_y - 6),
                    (heart_x + 6, heart_y),
                ]
                pygame.draw.polygon(screen, RED, points)
            
        elif self.state == "PAUSED":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(128)
            screen.blit(overlay, (0, 0))
            
            font = pygame.font.Font(None, 74)
            for i in range(3):
                pause_glow = font.render("PAUSA", True, (0, 0, 50 + i * 30))
                pause_rect = pause_glow.get_rect(center=(SCREEN_WIDTH/2 + random.randint(-1, 1), 150 + random.randint(-1, 1)))
                screen.blit(pause_glow, pause_rect)
            
            pause_text = font.render("PAUSA", True, WHITE)
            pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH/2, 150))
            screen.blit(pause_text, pause_rect)
            
            self.resume_button.draw(screen)
            self.menu_button.draw(screen)
            
        elif self.state == "GAME_OVER":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(128)
            screen.blit(overlay, (0, 0))
            
            font = pygame.font.Font(None, 48)
            if self.lives <= 0:
                game_over_text = "¡Game Over! ¡Te quedaste sin vidas!"
                game_over_color = RED
            else:
                game_over_text = "¡Felicidades! ¡Has completado todos los niveles!"
                game_over_color = GREEN
            
            for i in range(3):
                glow_text = font.render(game_over_text, True, (50 + i * 30, 0, 0) if self.lives <= 0 else (0, 50 + i * 30, 0))
                text_rect = glow_text.get_rect(center=(SCREEN_WIDTH/2 + random.randint(-1, 1), 150 + random.randint(-1, 1)))
                screen.blit(glow_text, text_rect)
            
            text = font.render(game_over_text, True, game_over_color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH/2, 150))
            screen.blit(text, text_rect)
            
            score_text = font.render(f'Puntuación Final: {self.score}', True, WHITE)
            score_rect = score_text.get_rect(center=(SCREEN_WIDTH/2, 220))
            screen.blit(score_text, score_rect)
            
            self.restart_button.draw(screen)
            self.menu_button.draw(screen)
        
        pygame.display.flip()

    def handle_input(self, event):
        if self.state == "MENU":
            if self.start_button.handle_event(event):
                self.state = "PLAYING"
                self.reset_game()
                
        elif self.state == "PLAYING":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.player.jump()
                elif event.key == pygame.K_ESCAPE:
                    self.state = "PAUSED"
                    
        elif self.state == "PAUSED":
            if self.resume_button.handle_event(event):
                self.state = "PLAYING"
            elif self.menu_button.handle_event(event):
                self.state = "MENU"
                
        elif self.state == "GAME_OVER":
            if self.restart_button.handle_event(event):
                self.reset_game()
                self.state = "PLAYING"
            elif self.menu_button.handle_event(event):
                self.state = "MENU"

game = Game()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        game.handle_input(event)
    
    game.update()
    
    game.draw()
    
    clock.tick(FPS)

pygame.quit()
