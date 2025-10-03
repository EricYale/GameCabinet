# Symbiosis Garden is a cooperative plant growing art experience where two players
# control the growth direction using joysticks. The plant grows continuously and
# responds to the average direction of both joysticks. Players can add flowers
# and create branch points. When the plant reaches screen edges, it branches to
# previously created bud points and continues growing from there.

import pygame
import serial
import math
import random
import time

pygame.init()

# Colors
DEEP_GREEN = (20, 60, 30)
SOFT_GREEN = (50, 120, 60)
BRIGHT_GREEN = (80, 200, 100)
FLOWER_COLORS = [
    (255, 100, 150),  # Pink
    (255, 200, 50),   # Yellow
    (150, 100, 255),  # Purple
    (255, 150, 100),  # Orange
    (100, 200, 255),  # Blue
    (255, 255, 150),  # Light Yellow
]
STEM_COLOR = (60, 140, 80)
BACKGROUND_BASE = (15, 25, 20)

# Screen setup
info = pygame.display.Info()
SCREEN_WIDTH, SCREEN_HEIGHT = info.current_w, info.current_h
SCALE_FACTOR = min(SCREEN_WIDTH / 1280.0, 1.0)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Symbiosis Garden")

# Serial setup
try:
    ser = serial.Serial("/dev/ttyUSB0", 115200, timeout=0.01)
except serial.SerialException:
    ser = None
    print("Serial port not found. Running with keyboard controls.")

class PlantSegment:
    def __init__(self, x, y, angle, length):
        self.start_pos = pygame.Vector2(x, y)
        self.angle = angle
        self.length = length
        self.end_pos = self.start_pos + pygame.Vector2(
            math.cos(math.radians(angle)) * length,
            math.sin(math.radians(angle)) * length
        )
        self.thickness = 8 * SCALE_FACTOR
        self.age = 0
        
    def update(self, dt):
        self.age += dt
            
    def draw(self, surface):
        color_intensity = 200 + int(55 * math.sin(self.age * 0.5))
        color = (
            max(0, min(255, STEM_COLOR[0] + color_intensity - 200)),
            max(0, min(255, STEM_COLOR[1] + color_intensity - 200)),
            max(0, min(255, STEM_COLOR[2] + color_intensity - 200))
        )
        pygame.draw.line(surface, color, self.start_pos, self.end_pos, int(self.thickness))

class Flower:
    def __init__(self, x, y, color):
        self.pos = pygame.Vector2(x, y)
        self.color = color
        self.size = 0
        self.max_size = random.uniform(15, 25) * SCALE_FACTOR
        self.bloom_speed = random.uniform(3, 5)
        self.age = 0
        self.petals = random.randint(5, 8)
        
    def update(self, dt):
        self.age += dt
        if self.size < self.max_size:
            self.size = min(self.max_size, self.size + self.bloom_speed * dt)
            
    def draw(self, surface):
        if self.size <= 0:
            return
        
        sway = math.sin(self.age * 2) * 2
        current_pos = self.pos + pygame.Vector2(sway, 0)
        
        for i in range(self.petals):
            angle = (i / self.petals) * 2 * math.pi
            petal_pos = current_pos + pygame.Vector2(
                math.cos(angle) * self.size * 0.6,
                math.sin(angle) * self.size * 0.6
            )
            pygame.draw.circle(surface, self.color, petal_pos, int(self.size * 0.4))
            
        center_color = tuple(max(0, min(255, c + 50)) for c in self.color)
        pygame.draw.circle(surface, center_color, current_pos, int(self.size * 0.3))

class Bud:
    def __init__(self, x, y):
        self.pos = pygame.Vector2(x, y)
        self.size = 8 * SCALE_FACTOR
        self.age = 0
        self.used = False
        
    def update(self, dt):
        self.age += dt
            
    def draw(self, surface):
        if self.size <= 0:
            return
        pulse = 0.8 + 0.2 * math.sin(self.age * 3)
        if self.used:
            pulse *= 0.3
        bud_color = tuple(int(c * pulse) for c in BRIGHT_GREEN)
        pygame.draw.circle(surface, bud_color, self.pos, int(self.size))

def calculate_direction_from_joysticks(p1_x, p2_x):
    # Convert to -1 to 1 range
    p1_normalized = (p1_x - 2048) / 2048.0
    p2_normalized = (p2_x - 2048) / 2048.0
    
    # Average the directions
    avg_direction = (p1_normalized + p2_normalized) / 2
    
    # Convert to angle change (max 45 degrees)
    angle_change = avg_direction * 45
    
    return angle_change

def main():
    clock = pygame.time.Clock()
    running = True
    last_time = time.time()
    
    # Plant state
    plant_segments = []
    flowers = []
    buds = []
    
    # Growth parameters
    plant_base_x = SCREEN_WIDTH // 2
    plant_base_y = SCREEN_HEIGHT - 50 * SCALE_FACTOR
    current_angle = -90  # Start growing upward
    segment_length = 25 * SCALE_FACTOR
    
    # Game state
    growth_frame_counter = 0
    
    # Input states
    p1_button_pressed = False
    p2_button_pressed = False
    
    # Add initial root segment
    root_segment = PlantSegment(plant_base_x, plant_base_y, current_angle, segment_length)
    plant_segments.append(root_segment)
    current_growth_point = root_segment
    
    while running:
        current_time = time.time()
        dt = current_time - last_time
        last_time = current_time
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # Read input
        p1_joy_x, p2_joy_x = 2048, 2048  # Default neutral
        p1_button, p2_button = 1, 1      # Default unpressed
        
        if ser:
            while ser.in_waiting:
                try:
                    line = ser.readline().decode('utf-8').rstrip()
                    if line:
                        values = line.split("/")
                        if len(values) == 8:
                            p2_joy_x = int(values[1])
                            p1_joy_x = int(values[3])
                            p1_button = int(values[4])
                            p2_button = int(values[5])
                except (ValueError, IndexError):
                    pass
        else:
            # Keyboard controls
            keys = pygame.key.get_pressed()
            if keys[pygame.K_a]: p1_joy_x = 500
            if keys[pygame.K_d]: p1_joy_x = 3500
            if keys[pygame.K_LEFT]: p2_joy_x = 500
            if keys[pygame.K_RIGHT]: p2_joy_x = 3500
            if keys[pygame.K_SPACE]: p1_button = 0
            if keys[pygame.K_RETURN]: p2_button = 0
        
        # Calculate joystick direction
        angle_change = calculate_direction_from_joysticks(p1_joy_x, p2_joy_x)
        
        # Handle buttons
        if plant_segments:
            tip_pos = plant_segments[-1].end_pos
            
            # Player 1: Plant flowers
            if p1_button == 0 and not p1_button_pressed:
                color = random.choice(FLOWER_COLORS)
                flowers.append(Flower(tip_pos.x, tip_pos.y, color))
                p1_button_pressed = True
            elif p1_button == 1:
                p1_button_pressed = False
                
            # Player 2: Create buds
            if p2_button == 0 and not p2_button_pressed:
                buds.append(Bud(tip_pos.x, tip_pos.y))
                p2_button_pressed = True
            elif p2_button == 1:
                p2_button_pressed = False
        
        # GROW PLANT - Simple version
        growth_frame_counter += 1
        if growth_frame_counter % 10 == 0 and len(plant_segments) < 200:
            # Apply joystick direction
            current_angle += angle_change
            current_angle = max(-160, min(160, current_angle))
            
            # Check if would go off screen
            next_x = current_growth_point.end_pos.x + math.cos(math.radians(current_angle)) * segment_length
            next_y = current_growth_point.end_pos.y + math.sin(math.radians(current_angle)) * segment_length
            
            margin = 80
            would_hit_edge = (next_x < margin or next_x > SCREEN_WIDTH - margin or 
                             next_y < margin or next_y > SCREEN_HEIGHT - margin)
            
            if would_hit_edge and buds:
                # Branch to first unused bud
                for bud in buds:
                    if not bud.used:
                        bud.used = True
                        current_growth_point = PlantSegment(bud.pos.x, bud.pos.y, -45, segment_length)
                        plant_segments.append(current_growth_point)
                        current_angle = -45
                        break
            elif not would_hit_edge:
                # Normal growth
                new_segment = PlantSegment(
                    current_growth_point.end_pos.x,
                    current_growth_point.end_pos.y,
                    current_angle,
                    segment_length
                )
                plant_segments.append(new_segment)
                current_growth_point = new_segment
        
        # Update objects
        for segment in plant_segments:
            segment.update(dt)
        for flower in flowers:
            flower.update(dt)
        for bud in buds:
            bud.update(dt)
        
        # Render
        screen.fill(BACKGROUND_BASE)
        
        # Draw everything
        for segment in plant_segments:
            segment.draw(screen)
        for flower in flowers:
            flower.draw(screen)
        for bud in buds:
            bud.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == '__main__':
    main()