# This is a cooperative ball-bouncing game where two players work together to keep a
# ball bouncing in the center of the screen. Each player controls a paddle positioned
# on their side of the screen - Player 1 at the bottom, Player 2 at the top. The ball
# bounces between the paddles and players must coordinate to keep it in play. The
# orientation-agnostic design ensures both players have the same view regardless of
# which side of the cabinet they're sitting on.

# Players use their joystick X-axis to move their paddle left and right along their
# edge of the screen. When the ball approaches their paddle, they must position it
# correctly to bounce the ball back toward their partner. Good timing and positioning
# creates longer rallies, combo streaks, and satisfying visual effects. The goal is
# to work together to achieve the highest bounce count possible before the ball escapes.

import pygame
import serial
import math
import random
import time

pygame.init()

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 100, 100)
BLUE = (100, 100, 255)
GREEN = (100, 255, 100)
YELLOW = (255, 255, 100)
PURPLE = (255, 100, 255)
ORANGE = (255, 200, 100)

info = pygame.display.Info()
SCREEN_WIDTH, SCREEN_HEIGHT = info.current_w, info.current_h
SCALE_FACTOR = min(SCREEN_WIDTH / 1280.0, 1.0)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Bounce Together")
font = pygame.font.Font(None, int(64 * SCALE_FACTOR))
big_font = pygame.font.Font(None, int(96 * SCALE_FACTOR))

try:
    ser = serial.Serial("/dev/ttyUSB0", 115200, timeout=0.01)
except serial.SerialException:
    ser = None
    print("Serial port not found. Running with keyboard controls.")

class Ball:
    def __init__(self):
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT // 2
        self.vx = 200 * SCALE_FACTOR
        self.vy = -300 * SCALE_FACTOR
        self.radius = 15 * SCALE_FACTOR
        self.color = WHITE
        self.trail = []
        self.bounce_count = 0
        self.combo = 0
        self.speed_multiplier = 1.0
        
    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        self.vy += 800 * SCALE_FACTOR * dt
        
        self.trail.append((self.x, self.y))
        if len(self.trail) > 10:
            self.trail.pop(0)
            
        if self.y > SCREEN_HEIGHT + 100:
            return False
        return True
    
    def bounce(self, paddle_speed, perfect_hit=False):
        self.bounce_count += 1
        
        base_bounce = -400 * SCALE_FACTOR
        speed_bonus = abs(paddle_speed) * 100 * SCALE_FACTOR
        
        if perfect_hit:
            self.vy = base_bounce - speed_bonus * 1.5
            self.combo += 1
            self.color = [GREEN, YELLOW, PURPLE, ORANGE][min(3, self.combo // 3)]
        else:
            self.vy = base_bounce - speed_bonus
            self.combo = max(0, self.combo - 1)
            self.color = WHITE
            
        self.vx += random.uniform(-50, 50) * SCALE_FACTOR
        self.vx = max(-400 * SCALE_FACTOR, min(400 * SCALE_FACTOR, self.vx))
    
    def draw(self, surface):
        for i, (tx, ty) in enumerate(self.trail):
            alpha = i / len(self.trail)
            trail_radius = int(self.radius * alpha * 0.5)
            if trail_radius > 0:
                trail_color = [int(c * alpha) for c in self.color]
                pygame.draw.circle(surface, trail_color, (int(tx), int(ty)), trail_radius)
        
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.radius))
        
        if self.combo > 0:
            glow_radius = int(self.radius * (1 + self.combo * 0.1))
            glow_color = [min(255, c + 50) for c in self.color]
            pygame.draw.circle(surface, glow_color, (int(self.x), int(self.y)), glow_radius, 3)

class Paddle:
    def __init__(self, y, color, player_id):
        self.x = SCREEN_WIDTH // 2
        self.y = y
        self.target_x = self.x
        self.width = 120 * SCALE_FACTOR
        self.height = 20 * SCALE_FACTOR
        self.color = color
        self.player_id = player_id
        self.speed = 0
        self.last_x = self.x
        self.hits = 0
        self.perfect_hits = 0
        
    def update(self, dt, joy_input):
        self.target_x = SCREEN_WIDTH // 2 + joy_input * (SCREEN_WIDTH // 3)
        self.target_x = max(self.width // 2, min(SCREEN_WIDTH - self.width // 2, self.target_x))
        
        self.last_x = self.x
        self.x += (self.target_x - self.x) * 8 * dt
        self.speed = (self.x - self.last_x) / dt
        
    def check_collision(self, ball):
        if (abs(ball.x - self.x) < self.width // 2 + ball.radius and
            abs(ball.y - self.y) < self.height // 2 + ball.radius):
            
            hit_center = abs(ball.x - self.x) < self.width // 4
            
            if hit_center and abs(self.speed) > 50:
                self.perfect_hits += 1
                return True, True
            else:
                self.hits += 1
                return True, False
        return False, False
    
    def draw(self, surface):
        rect = pygame.Rect(self.x - self.width // 2, self.y - self.height // 2, 
                          self.width, self.height)
        pygame.draw.rect(surface, self.color, rect)
        
        if abs(self.speed) > 100:
            glow_rect = pygame.Rect(self.x - self.width // 2 - 5, self.y - self.height // 2 - 5,
                                   self.width + 10, self.height + 10)
            pygame.draw.rect(surface, [min(255, c + 100) for c in self.color], glow_rect, 3)

def draw_score(surface, ball, p1_paddle, p2_paddle):
    score_text = font.render(f"Bounces: {ball.bounce_count}", True, WHITE)
    surface.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 50 * SCALE_FACTOR))
    
    if ball.combo > 0:
        combo_text = font.render(f"COMBO x{ball.combo}!", True, YELLOW)
        surface.blit(combo_text, (SCREEN_WIDTH // 2 - combo_text.get_width() // 2, 100 * SCALE_FACTOR))
    
    p1_stats = f"P1: {p1_paddle.hits} hits, {p1_paddle.perfect_hits} perfect"
    p2_stats = f"P2: {p2_paddle.hits} hits, {p2_paddle.perfect_hits} perfect"
    
    p1_text = font.render(p1_stats, True, BLUE)
    p2_text = font.render(p2_stats, True, RED)
    
    surface.blit(p1_text, (50 * SCALE_FACTOR, SCREEN_HEIGHT - 100 * SCALE_FACTOR))
    surface.blit(p2_text, (50 * SCALE_FACTOR, SCREEN_HEIGHT - 60 * SCALE_FACTOR))

def draw_instructions(surface):
    instructions = [
        "Player 1 (Blue): Bottom paddle - move joystick left/right",
        "Player 2 (Red): Top paddle - move joystick left/right", 
        "Hit ball in center of paddle while moving for PERFECT hits",
        "Work together to keep the ball bouncing!"
    ]
    
    for i, instruction in enumerate(instructions):
        text = font.render(instruction, True, WHITE)
        surface.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 
                           SCREEN_HEIGHT - 200 * SCALE_FACTOR + i * 40 * SCALE_FACTOR))

def main():
    clock = pygame.time.Clock()
    running = True
    game_active = True
    
    ball = Ball()
    p1_paddle = Paddle(SCREEN_HEIGHT - 50 * SCALE_FACTOR, BLUE, 1)
    p2_paddle = Paddle(50 * SCALE_FACTOR, RED, 2)
    
    particles = []
    game_over_time = 0
    
    last_time = time.time()
    
    while running:
        current_time = time.time()
        dt = current_time - last_time
        last_time = current_time
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        p1_joy_x = 0
        p1_joy_y = 0
        p2_joy_x = 0
        p2_joy_y = 0
        p1_button = 1
        p2_button = 1
        p1_switch = 0
        p2_switch = 1
        
        if ser:
            while ser.in_waiting:
                try:
                    line = ser.readline().decode('utf-8').rstrip()
                    if line:
                        values = line.split("/")
                        if len(values) == 8:
                            p2_joy_x = (int(values[1]) - 2048) / 2048.0
                            p1_joy_x = (int(values[3]) - 2048) / 2048.0
                            p1_button = int(values[4])
                            p2_button = int(values[5])
                            p1_switch = int(values[6])
                            p2_switch = int(values[7])
                except (ValueError, IndexError):
                    pass
        else:
            keys = pygame.key.get_pressed()
            p1_joy_x = -0.8 if keys[pygame.K_a] else (0.8 if keys[pygame.K_d] else 0)
            p2_joy_x = -0.8 if keys[pygame.K_LEFT] else (0.8 if keys[pygame.K_RIGHT] else 0)
            p1_button = 0 if keys[pygame.K_SPACE] else 1
            p2_button = 0 if keys[pygame.K_RETURN] else 1
            p1_switch = 1 if keys[pygame.K_q] else 0
            p2_switch = 0 if keys[pygame.K_e] else 1
        
        if not game_active:
            any_input = (abs(p1_joy_x) > 0.3 or abs(p2_joy_x) > 0.3 or 
                        p1_button == 0 or p2_button == 0 or 
                        p1_switch == 1 or p2_switch == 0)
            
            if any_input:
                ball = Ball()
                p1_paddle = Paddle(SCREEN_HEIGHT - 50 * SCALE_FACTOR, BLUE, 1)
                p2_paddle = Paddle(50 * SCALE_FACTOR, RED, 2)
                particles = []
                game_active = True
        
        if game_active:
            p1_paddle.update(dt, p1_joy_x)
            p2_paddle.update(dt, p2_joy_x)
            
            game_active = ball.update(dt)
            
            hit1, perfect1 = p1_paddle.check_collision(ball)
            hit2, perfect2 = p2_paddle.check_collision(ball)
            
            if hit1 or hit2:
                paddle = p1_paddle if hit1 else p2_paddle
                ball.bounce(paddle.speed, perfect1 or perfect2)
                
                if perfect1 or perfect2:
                    for _ in range(10):
                        particles.append({
                            'x': ball.x,
                            'y': ball.y,
                            'vx': random.uniform(-200, 200) * SCALE_FACTOR,
                            'vy': random.uniform(-200, 200) * SCALE_FACTOR,
                            'life': 1.0,
                            'color': ball.color
                        })
            
            if ball.x < 0 or ball.x > SCREEN_WIDTH:
                ball.vx = -ball.vx
                ball.x = max(ball.radius, min(SCREEN_WIDTH - ball.radius, ball.x))
            
            if ball.y < 0 or ball.y > SCREEN_HEIGHT:
                game_active = False
        else:
            if game_over_time == 0:
                game_over_time = current_time
        
        particles = [p for p in particles if p['life'] > 0]
        for particle in particles:
            particle['x'] += particle['vx'] * dt
            particle['y'] += particle['vy'] * dt
            particle['life'] -= dt
        
        screen.fill(BLACK)
        
        pygame.draw.line(screen, WHITE, (0, SCREEN_HEIGHT // 2), (SCREEN_WIDTH, SCREEN_HEIGHT // 2), 2)
        
        if game_active:
            ball.draw(screen)
            p1_paddle.draw(screen)
            p2_paddle.draw(screen)
            draw_score(screen, ball, p1_paddle, p2_paddle)
        else:
            game_over_text = big_font.render("GAME OVER", True, RED)
            screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, 
                                        SCREEN_HEIGHT // 2 - 100 * SCALE_FACTOR))
            
            final_score = font.render(f"Final Score: {ball.bounce_count} bounces", True, WHITE)
            screen.blit(final_score, (SCREEN_WIDTH // 2 - final_score.get_width() // 2,
                                     SCREEN_HEIGHT // 2 - 50 * SCALE_FACTOR))
            
            restart_text = font.render("Move joystick, press button, or flip switch to play again", True, WHITE)
            screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2,
                                      SCREEN_HEIGHT // 2 + 50 * SCALE_FACTOR))
        
        for particle in particles:
            alpha = particle['life']
            size = max(1, int(8 * SCALE_FACTOR * alpha))
            color = [int(c * alpha) for c in particle['color']]
            pygame.draw.circle(screen, color, (int(particle['x']), int(particle['y'])), size)
        
        if game_active and ball.bounce_count == 0:
            draw_instructions(screen)
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == '__main__':
    main()