# This game is a digital tug-of-war battle called "The Pulse" where two players face off
# using rhythm, timing, and psychological strategy. Players control a shared energy pulse
# on a horizontal bar using their joysticks, with the goal of pulling it to their side.
# The game emphasizes steady, intentional pulls over frantic movement, with button boosts
# for strategic timing and toggle switches that change between power and agility modes.

# The core mechanics involve continuous joystick pulling (X-axis), timed button boosts that
# can backfire if mistimed, and mode switching between power (slow/strong) and agility
# (fast/weak) states. The visual design features a plasma-like energy bar with a pulsing
# orb that responds to player input, creating tension through audio-visual feedback and
# dynamic color changes as momentum shifts between players.

import pygame
import serial
import math
import time

pygame.init()

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)

info = pygame.display.Info()
SCREEN_WIDTH, SCREEN_HEIGHT = info.current_w, info.current_h
SCALE_FACTOR = min(SCREEN_WIDTH / 1280.0, 1.0)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("The Pulse")
font = pygame.font.Font(None, int(74 * SCALE_FACTOR))
small_font = pygame.font.Font(None, int(36 * SCALE_FACTOR))

try:
    ser = serial.Serial("/dev/ttyUSB0", 115200, timeout=0.01)
except serial.SerialException:
    ser = None
    print("Serial port not found. Running with keyboard controls.")

class Player:
    def __init__(self, player_id, color):
        self.player_id = player_id
        self.color = color
        self.pull_force = 0
        self.mode = "agility"
        self.grip_penalty = 0
        self.boost_cooldown = 0
        self.last_boost_time = 0
        self.fatigue = 0
        self.last_pull_direction = 0
        self.consistent_pull_time = 0
        self.spam_protection = 0
        
    def update(self, dt, joystick_input, button_pressed, switch_state, pulse_position):
        if self.grip_penalty > 0:
            self.grip_penalty -= dt
            self.pull_force = max(0, self.pull_force - dt * 3)
            return
            
        if self.spam_protection > 0:
            self.spam_protection -= dt
            self.pull_force = max(0, self.pull_force - dt * 2)
            return
            
        if self.boost_cooldown > 0:
            self.boost_cooldown -= dt
            
        self.mode = "power" if switch_state else "agility"
        
        current_direction = 1 if abs(joystick_input) > 0.3 else 0
        if self.player_id == 1:
            current_direction = 1 if joystick_input < -0.3 else 0
        else:
            current_direction = 1 if joystick_input > 0.3 else 0
            
        if current_direction != self.last_pull_direction and current_direction != 0:
            if self.consistent_pull_time < 0.5:
                self.spam_protection = 1.0
                
        if current_direction == self.last_pull_direction and current_direction != 0:
            self.consistent_pull_time += dt
        else:
            self.consistent_pull_time = 0
            
        self.last_pull_direction = current_direction
        
        if current_direction:
            base_force = 1.0 if self.mode == "agility" else 0.6
            speed_multiplier = 1.5 if self.mode == "agility" else 2.5
            consistency_bonus = min(self.consistent_pull_time * 0.5, 1.0)
            
            target_force = (base_force + consistency_bonus) * speed_multiplier
            self.pull_force = min(target_force, self.pull_force + dt * 4)
            
            self.fatigue = min(1.0, self.fatigue + dt * 0.3)
        else:
            self.pull_force = max(0, self.pull_force - dt * 2)
            self.fatigue = max(0, self.fatigue - dt * 0.5)
            
        self.pull_force *= (1.0 - self.fatigue * 0.3)
        
        if button_pressed and self.boost_cooldown <= 0:
            self.handle_boost(pulse_position)
            
    def handle_boost(self, pulse_position):
        optimal_zone = 0.3
        player_side = -1 if self.player_id == 1 else 1
        
        if (player_side * pulse_position) > optimal_zone:
            self.pull_force += 3.0
            self.boost_cooldown = 1.5
        else:
            self.grip_penalty = 0.8
            self.boost_cooldown = 2.0

class Pulse:
    def __init__(self):
        self.position = 0.0
        self.velocity = 0.0
        self.size = 20 * SCALE_FACTOR
        self.glow_intensity = 0.5
        self.pulse_phase = 0
        
    def update(self, dt, p1_force, p2_force):
        net_force = -p1_force + p2_force
        acceleration = net_force * 0.5
        
        self.velocity += acceleration * dt
        self.velocity *= 0.98
        self.velocity = max(-3, min(3, self.velocity))
        
        self.position += self.velocity * dt
        self.position = max(-1.0, min(1.0, self.position))
        
        self.glow_intensity = 0.5 + abs(net_force) * 0.2
        self.pulse_phase += dt * (1 + abs(self.velocity))
        
    def draw(self, surface):
        bar_width = SCREEN_WIDTH * 0.8
        bar_height = 20 * SCALE_FACTOR
        bar_x = SCREEN_WIDTH * 0.1
        bar_y = SCREEN_HEIGHT // 2 - bar_height // 2
        
        pygame.draw.rect(surface, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)
        
        p1_fill = max(0, -self.position) * bar_width / 2
        p2_fill = max(0, self.position) * bar_width / 2
        
        if p1_fill > 0:
            pygame.draw.rect(surface, BLUE, (bar_x, bar_y, p1_fill, bar_height))
        if p2_fill > 0:
            pygame.draw.rect(surface, RED, (bar_x + bar_width - p2_fill, bar_y, p2_fill, bar_height))
            
        pulse_x = bar_x + bar_width // 2 + self.position * (bar_width // 2 - self.size)
        pulse_y = bar_y + bar_height // 2
        
        glow_size = self.size * (1 + math.sin(self.pulse_phase * 5) * 0.3)
        glow_color = [255, 255, 255]
        
        if self.position < -0.3:
            glow_color = [100, 100, 255]
        elif self.position > 0.3:
            glow_color = [255, 100, 100]
            
        for i in range(5):
            alpha = (5 - i) * 0.2 * self.glow_intensity
            radius = glow_size * (1 + i * 0.3)
            color = [int(c * alpha) for c in glow_color]
            pygame.draw.circle(surface, color, (int(pulse_x), int(pulse_y)), int(radius))
            
        pygame.draw.circle(surface, WHITE, (int(pulse_x), int(pulse_y)), int(self.size), 2)

def draw_player_status(surface, player, side):
    status_x = 50 * SCALE_FACTOR if side == "left" else SCREEN_WIDTH - 200 * SCALE_FACTOR
    status_y = 50 * SCALE_FACTOR
    
    mode_text = f"Mode: {player.mode.upper()}"
    mode_surface = small_font.render(mode_text, True, player.color)
    surface.blit(mode_surface, (status_x, status_y))
    
    force_bar_width = 100 * SCALE_FACTOR
    force_bar_height = 10 * SCALE_FACTOR
    force_y = status_y + 40 * SCALE_FACTOR
    
    pygame.draw.rect(surface, WHITE, (status_x, force_y, force_bar_width, force_bar_height), 1)
    force_fill = player.pull_force / 4.0 * force_bar_width
    pygame.draw.rect(surface, player.color, (status_x, force_y, force_fill, force_bar_height))
    
    if player.grip_penalty > 0:
        penalty_text = "GRIP PENALTY!"
        penalty_surface = small_font.render(penalty_text, True, RED)
        surface.blit(penalty_surface, (status_x, force_y + 20 * SCALE_FACTOR))
    elif player.spam_protection > 0:
        spam_text = "TOO FAST!"
        spam_surface = small_font.render(spam_text, True, YELLOW)
        surface.blit(spam_surface, (status_x, force_y + 20 * SCALE_FACTOR))
    elif player.boost_cooldown > 0:
        cooldown_text = f"Boost: {player.boost_cooldown:.1f}s"
        cooldown_surface = small_font.render(cooldown_text, True, WHITE)
        surface.blit(cooldown_surface, (status_x, force_y + 20 * SCALE_FACTOR))

def main():
    clock = pygame.time.Clock()
    running = True
    
    player1 = Player(1, BLUE)
    player2 = Player(2, RED)
    pulse = Pulse()
    
    p1_button_pressed = False
    p2_button_pressed = False
    
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
        p2_joy_x = 0
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
            p1_joy_x = -1 if keys[pygame.K_a] else (1 if keys[pygame.K_d] else 0)
            p2_joy_x = -1 if keys[pygame.K_LEFT] else (1 if keys[pygame.K_RIGHT] else 0)
            p1_button = 0 if keys[pygame.K_SPACE] else 1
            p2_button = 0 if keys[pygame.K_RETURN] else 1
            p1_switch = 1 if keys[pygame.K_w] else 0
            p2_switch = 0 if keys[pygame.K_UP] else 1
            
        p1_button_now_pressed = (p1_button == 0 and not p1_button_pressed)
        p2_button_now_pressed = (p2_button == 0 and not p2_button_pressed)
        p1_button_pressed = (p1_button == 0)
        p2_button_pressed = (p2_button == 0)
        
        player1.update(dt, p1_joy_x, p1_button_now_pressed, p1_switch == 1, pulse.position)
        player2.update(dt, p2_joy_x, p2_button_now_pressed, p2_switch == 0, pulse.position)
        
        pulse.update(dt, player1.pull_force, player2.pull_force)
        
        screen.fill(BLACK)
        
        pulse.draw(screen)
        draw_player_status(screen, player1, "left")
        draw_player_status(screen, player2, "right")
        
        if abs(pulse.position) >= 0.9:
            winner = "Player 1" if pulse.position < 0 else "Player 2"
            winner_color = BLUE if pulse.position < 0 else RED
            
            win_text = font.render(f"{winner} Wins!", True, winner_color)
            win_rect = win_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100 * SCALE_FACTOR))
            screen.blit(win_text, win_rect)
            
            pygame.display.flip()
            pygame.time.wait(3000)
            
            pulse.position = 0.0
            pulse.velocity = 0.0
            player1.pull_force = 0
            player2.pull_force = 0
            player1.grip_penalty = 0
            player2.grip_penalty = 0
            player1.boost_cooldown = 0
            player2.boost_cooldown = 0
            
        pygame.display.flip()
        clock.tick(60)
        
    pygame.quit()

if __name__ == '__main__':
    main()