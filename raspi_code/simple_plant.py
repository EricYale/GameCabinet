# This is a simple cooperative plant growing game where two players work together to
# nurture a shared digital plant. Player 1 controls sunlight and water using their
# joystick, while Player 2 controls nutrients and wind. Both players must coordinate
# their actions to help the plant grow tall and healthy. The game emphasizes clear
# visual feedback and intuitive controls that make cooperation natural and rewarding.

# The plant grows automatically over time, but players can boost its growth by providing
# the right resources at the right moments. Sunlight makes the plant photosynthesize,
# water helps roots grow, nutrients strengthen the stem, and gentle wind spreads seeds.
# Players press buttons to activate special abilities like blooming flowers or growing
# new branches. The goal is simply to grow the most beautiful plant possible together.

import pygame
import serial
import math
import random
import time

pygame.init()

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (34, 139, 34)
BROWN = (139, 69, 19)
YELLOW = (255, 255, 0)
BLUE = (135, 206, 235)
RED = (255, 99, 71)
PINK = (255, 182, 193)
ORANGE = (255, 165, 0)
LIGHT_GREEN = (144, 238, 144)

info = pygame.display.Info()
SCREEN_WIDTH, SCREEN_HEIGHT = info.current_w, info.current_h
SCALE_FACTOR = min(SCREEN_WIDTH / 1280.0, 1.0)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Grow Together")
font = pygame.font.Font(None, int(48 * SCALE_FACTOR))
small_font = pygame.font.Font(None, int(32 * SCALE_FACTOR))

try:
    ser = serial.Serial("/dev/ttyUSB0", 115200, timeout=0.01)
except serial.SerialException:
    ser = None
    print("Serial port not found. Running with keyboard controls.")

class Plant:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.height = 20 * SCALE_FACTOR
        self.width = 4 * SCALE_FACTOR
        self.health = 50
        self.max_health = 100
        self.branches = []
        self.flowers = []
        self.leaves = []
        self.growth_rate = 0.5
        self.last_growth = time.time()
        self.sunlight_level = 0
        self.water_level = 0
        self.nutrients_level = 0
        self.wind_level = 0
        self.happiness = 50
        
        for i in range(3):
            leaf_x = self.x + random.randint(-20, 20) * SCALE_FACTOR
            leaf_y = self.y - self.height + random.randint(-10, 10) * SCALE_FACTOR
            self.leaves.append({'x': leaf_x, 'y': leaf_y, 'size': 8 * SCALE_FACTOR})
    
    def update(self, dt, sunlight, water, nutrients, wind):
        self.sunlight_level = max(0, min(100, self.sunlight_level + (sunlight - 50) * dt * 2))
        self.water_level = max(0, min(100, self.water_level + (water - 50) * dt * 2))
        self.nutrients_level = max(0, min(100, self.nutrients_level + (nutrients - 50) * dt * 2))
        self.wind_level = max(0, min(100, self.wind_level + (wind - 50) * dt * 2))
        
        ideal_sunlight = 70
        ideal_water = 60
        ideal_nutrients = 50
        ideal_wind = 30
        
        sunlight_score = 100 - abs(self.sunlight_level - ideal_sunlight)
        water_score = 100 - abs(self.water_level - ideal_water)
        nutrients_score = 100 - abs(self.nutrients_level - ideal_nutrients)
        wind_score = 100 - abs(self.wind_level - ideal_wind)
        
        self.happiness = (sunlight_score + water_score + nutrients_score + wind_score) / 4
        
        if self.happiness > 60:
            self.health = min(self.max_health, self.health + dt * 20)
            if time.time() - self.last_growth > 2.0:
                self.grow()
                self.last_growth = time.time()
        elif self.happiness < 30:
            self.health = max(0, self.health - dt * 10)
    
    def grow(self):
        old_height = self.height
        self.height += random.randint(5, 15) * SCALE_FACTOR
        self.width = max(self.width, self.height * 0.1)
        
        if random.random() < 0.3 and len(self.leaves) < 10:
            leaf_x = self.x + random.randint(-30, 30) * SCALE_FACTOR
            leaf_y = self.y - self.height + random.randint(-20, 20) * SCALE_FACTOR
            self.leaves.append({'x': leaf_x, 'y': leaf_y, 'size': random.randint(6, 12) * SCALE_FACTOR})
    
    def add_flower(self):
        if len(self.flowers) < 8:
            flower_x = self.x + random.randint(-25, 25) * SCALE_FACTOR
            flower_y = self.y - self.height + random.randint(-30, 10) * SCALE_FACTOR
            color = random.choice([PINK, YELLOW, RED, ORANGE])
            self.flowers.append({'x': flower_x, 'y': flower_y, 'color': color, 'size': random.randint(8, 15) * SCALE_FACTOR})
    
    def add_branch(self):
        if len(self.branches) < 6:
            branch_start_y = self.y - random.randint(int(self.height * 0.3), int(self.height * 0.8))
            branch_length = random.randint(20, 40) * SCALE_FACTOR
            branch_angle = random.choice([-45, -30, 30, 45])
            
            end_x = self.x + math.cos(math.radians(branch_angle)) * branch_length
            end_y = branch_start_y + math.sin(math.radians(branch_angle)) * branch_length
            
            self.branches.append({
                'start_x': self.x,
                'start_y': branch_start_y,
                'end_x': end_x,
                'end_y': end_y,
                'thickness': random.randint(2, 4) * SCALE_FACTOR
            })
    
    def draw(self, surface):
        stem_color = GREEN if self.health > 30 else BROWN
        stem_thickness = max(2, int(self.width))
        
        pygame.draw.line(surface, stem_color, 
                        (self.x, self.y), 
                        (self.x, self.y - self.height), 
                        stem_thickness)
        
        for branch in self.branches:
            pygame.draw.line(surface, stem_color,
                           (branch['start_x'], branch['start_y']),
                           (branch['end_x'], branch['end_y']),
                           branch['thickness'])
        
        for leaf in self.leaves:
            leaf_color = LIGHT_GREEN if self.health > 50 else GREEN
            pygame.draw.circle(surface, leaf_color, 
                             (int(leaf['x']), int(leaf['y'])), 
                             int(leaf['size']))
        
        for flower in self.flowers:
            pygame.draw.circle(surface, flower['color'],
                             (int(flower['x']), int(flower['y'])),
                             int(flower['size']))
            pygame.draw.circle(surface, YELLOW,
                             (int(flower['x']), int(flower['y'])),
                             int(flower['size'] * 0.4))

def draw_resource_bars(surface, plant):
    bar_width = 200 * SCALE_FACTOR
    bar_height = 20 * SCALE_FACTOR
    start_x = 30 * SCALE_FACTOR
    start_y = 50 * SCALE_FACTOR
    
    resources = [
        ("Sunlight", plant.sunlight_level, YELLOW),
        ("Water", plant.water_level, BLUE),
        ("Nutrients", plant.nutrients_level, BROWN),
        ("Wind", plant.wind_level, WHITE)
    ]
    
    for i, (name, level, color) in enumerate(resources):
        y = start_y + i * 35 * SCALE_FACTOR
        
        pygame.draw.rect(surface, WHITE, (start_x, y, bar_width, bar_height), 2)
        fill_width = (level / 100) * bar_width
        pygame.draw.rect(surface, color, (start_x, y, fill_width, bar_height))
        
        text = small_font.render(f"{name}: {int(level)}", True, WHITE)
        surface.blit(text, (start_x, y - 25 * SCALE_FACTOR))

def draw_happiness_meter(surface, plant):
    meter_x = SCREEN_WIDTH - 250 * SCALE_FACTOR
    meter_y = 50 * SCALE_FACTOR
    meter_width = 200 * SCALE_FACTOR
    meter_height = 30 * SCALE_FACTOR
    
    pygame.draw.rect(surface, WHITE, (meter_x, meter_y, meter_width, meter_height), 2)
    
    fill_width = (plant.happiness / 100) * meter_width
    if plant.happiness > 70:
        color = GREEN
    elif plant.happiness > 40:
        color = YELLOW
    else:
        color = RED
    
    pygame.draw.rect(surface, color, (meter_x, meter_y, fill_width, meter_height))
    
    text = small_font.render(f"Happiness: {int(plant.happiness)}", True, WHITE)
    surface.blit(text, (meter_x, meter_y - 30 * SCALE_FACTOR))
    
    health_text = small_font.render(f"Health: {int(plant.health)}/{plant.max_health}", True, WHITE)
    surface.blit(health_text, (meter_x, meter_y + 40 * SCALE_FACTOR))

def draw_instructions(surface):
    instructions = [
        "Player 1: Move joystick to control sunlight & water",
        "Player 2: Move joystick to control nutrients & wind", 
        "Press buttons to add flowers & branches!",
        "Work together to keep your plant happy!"
    ]
    
    for i, instruction in enumerate(instructions):
        text = small_font.render(instruction, True, WHITE)
        surface.blit(text, (30 * SCALE_FACTOR, SCREEN_HEIGHT - 120 * SCALE_FACTOR + i * 25 * SCALE_FACTOR))

def main():
    clock = pygame.time.Clock()
    running = True
    
    plant = Plant(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100 * SCALE_FACTOR)
    
    p1_button_pressed = False
    p2_button_pressed = False
    
    particles = []
    
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
            p1_joy_y = -0.8 if keys[pygame.K_w] else (0.8 if keys[pygame.K_s] else 0)
            p2_joy_x = -0.8 if keys[pygame.K_LEFT] else (0.8 if keys[pygame.K_RIGHT] else 0)
            p2_joy_y = -0.8 if keys[pygame.K_UP] else (0.8 if keys[pygame.K_DOWN] else 0)
            p1_button = 0 if keys[pygame.K_SPACE] else 1
            p2_button = 0 if keys[pygame.K_RETURN] else 1
        
        sunlight = 50 + p1_joy_y * 50
        water = 50 + p1_joy_x * 50
        nutrients = 50 + p2_joy_y * 50
        wind = 50 + p2_joy_x * 50
        
        plant.update(dt, sunlight, water, nutrients, wind)
        
        p1_button_now = (p1_button == 0 and not p1_button_pressed)
        p2_button_now = (p2_button == 0 and not p2_button_pressed)
        p1_button_pressed = (p1_button == 0)
        p2_button_pressed = (p2_button == 0)
        
        if p1_button_now:
            plant.add_flower()
        
        if p2_button_now:
            plant.add_branch()
        
        if plant.happiness > 80 and random.random() < 0.02:
            for _ in range(3):
                particles.append({
                    'x': plant.x + random.randint(-50, 50) * SCALE_FACTOR,
                    'y': plant.y - plant.height + random.randint(-20, 20) * SCALE_FACTOR,
                    'vx': random.uniform(-30, 30) * SCALE_FACTOR,
                    'vy': random.uniform(-50, -20) * SCALE_FACTOR,
                    'life': 2.0,
                    'color': random.choice([YELLOW, PINK, WHITE])
                })
        
        particles = [p for p in particles if p['life'] > 0]
        for particle in particles:
            particle['x'] += particle['vx'] * dt
            particle['y'] += particle['vy'] * dt
            particle['life'] -= dt
        
        screen.fill(BLACK)
        
        ground_y = SCREEN_HEIGHT - 50 * SCALE_FACTOR
        pygame.draw.line(screen, BROWN, (0, ground_y), (SCREEN_WIDTH, ground_y), 5)
        
        plant.draw(screen)
        
        for particle in particles:
            alpha = int(255 * (particle['life'] / 2.0))
            size = max(1, int(4 * SCALE_FACTOR * (particle['life'] / 2.0)))
            pygame.draw.circle(screen, particle['color'], 
                             (int(particle['x']), int(particle['y'])), size)
        
        draw_resource_bars(screen, plant)
        draw_happiness_meter(screen, plant)
        draw_instructions(screen)
        
        if plant.happiness > 90:
            sparkle_text = font.render("Your plant is thriving! ✨", True, YELLOW)
            text_rect = sparkle_text.get_rect(center=(SCREEN_WIDTH//2, 100 * SCALE_FACTOR))
            screen.blit(sparkle_text, text_rect)
        elif plant.happiness < 20:
            sad_text = font.render("Your plant needs help! 💔", True, RED)
            text_rect = sad_text.get_rect(center=(SCREEN_WIDTH//2, 100 * SCALE_FACTOR))
            screen.blit(sad_text, text_rect)
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == '__main__':
    main()