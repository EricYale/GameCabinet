# Symbiosis Garden is a meditative cooperative art experience where two players
# nurture a shared digital plant through synchronized interaction. Players use
# their joysticks to collectively guide the plant's growth direction - when both
# players point in similar directions, the plant grows that way, but if they
# disagree, the plant pauses until they find harmony. This creates a natural
# dialogue through movement. The buttons allow players to add colorful flowers
# along the plant's stem, while the toggle switches control the growth state -
# both players must agree to grow (switches up) or rest (switches down).

# The implementation uses particle systems for organic, flowing growth patterns
# and a color palette that shifts based on the players' harmony level. The plant
# grows as a series of connected segments, each influenced by the average joystick
# input when there's agreement. Flowers bloom as animated sprites at button press
# locations, with colors cycling through a natural spectrum. The background
# subtly shifts to reflect the garden's health and the players' collaboration,
# creating a living, breathing digital ecosystem that responds to human connection.

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
        self.thickness = max(3, 15 * SCALE_FACTOR)
        self.age = 0
        self.growth_animation = 0
        
    def update(self, dt):
        self.age += dt
        if self.growth_animation < 1.0:
            self.growth_animation = min(1.0, self.growth_animation + dt * 2)
            
    def draw(self, surface):
        if self.growth_animation <= 0:
            return
            
        current_length = self.length * self.growth_animation
        current_end = self.start_pos + pygame.Vector2(
            math.cos(math.radians(self.angle)) * current_length,
            math.sin(math.radians(self.angle)) * current_length
        )
        
        # Draw segment with slight transparency for organic feel
        color_intensity = 200 + int(55 * math.sin(self.age * 0.5))
        color = (
            max(0, min(255, STEM_COLOR[0] + color_intensity - 200)),
            max(0, min(255, STEM_COLOR[1] + color_intensity - 200)),
            max(0, min(255, STEM_COLOR[2] + color_intensity - 200))
        )
        
        pygame.draw.line(surface, color, self.start_pos, current_end, int(self.thickness))

class Flower:
    def __init__(self, x, y, color):
        self.pos = pygame.Vector2(x, y)
        self.color = color
        self.size = 0
        self.max_size = random.uniform(15, 25) * SCALE_FACTOR
        self.bloom_speed = random.uniform(3, 5)
        self.sway_offset = random.uniform(0, math.pi * 2)
        self.age = 0
        self.petals = random.randint(5, 8)
        
    def update(self, dt):
        self.age += dt
        if self.size < self.max_size:
            self.size = min(self.max_size, self.size + self.bloom_speed * dt)
            
    def draw(self, surface):
        if self.size <= 0:
            return
            
        # Gentle swaying
        sway = math.sin(self.age * 2 + self.sway_offset) * 2
        current_pos = self.pos + pygame.Vector2(sway, 0)
        
        # Draw petals
        for i in range(self.petals):
            angle = (i / self.petals) * 2 * math.pi
            petal_pos = current_pos + pygame.Vector2(
                math.cos(angle) * self.size * 0.6,
                math.sin(angle) * self.size * 0.6
            )
            pygame.draw.circle(surface, self.color, petal_pos, int(self.size * 0.4))
            
        # Draw center
        center_color = tuple(max(0, min(255, c + 50)) for c in self.color)
        pygame.draw.circle(surface, center_color, current_pos, int(self.size * 0.3))

class HarmonyParticle:
    def __init__(self, x, y):
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(
            random.uniform(-50, 50) * SCALE_FACTOR,
            random.uniform(-100, -20) * SCALE_FACTOR
        )
        self.life = 1.0
        self.decay_rate = random.uniform(0.5, 1.0)
        self.size = random.uniform(2, 6) * SCALE_FACTOR
        
    def update(self, dt):
        self.pos += self.vel * dt
        self.life -= self.decay_rate * dt
        self.vel.y += 20 * dt  # Slight gravity
        
    def draw(self, surface):
        if self.life <= 0:
            return
        alpha = int(255 * self.life)
        color = (*BRIGHT_GREEN, alpha)
        
        # Create surface with per-pixel alpha
        particle_surf = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
        pygame.draw.circle(particle_surf, color, (int(self.size), int(self.size)), int(self.size))
        surface.blit(particle_surf, (self.pos.x - self.size, self.pos.y - self.size), special_flags=pygame.BLEND_ALPHA_SDL2)

def calculate_joystick_harmony(p1_x, p2_x):
    """Calculate growth direction and harmony from joystick inputs"""
    # Convert to -1 to 1 range
    p1_normalized = (p1_x - 2048) / 2048.0
    p2_normalized = (p2_x - 2048) / 2048.0
    
    # Only consider significant movements
    if abs(p1_normalized) < 0.3:
        p1_normalized = 0
    if abs(p2_normalized) < 0.3:
        p2_normalized = 0
        
    # Calculate agreement - if both are moving in similar direction
    if p1_normalized == 0 and p2_normalized == 0:
        return 0, 0, True  # Both neutral = harmony
    elif p1_normalized == 0 or p2_normalized == 0:
        return 0, 0, False  # One active, one not = no harmony
    elif (p1_normalized > 0) == (p2_normalized > 0):
        # Same direction
        avg_direction = (p1_normalized + p2_normalized) / 2
        harmony_strength = 1.0 - abs(p1_normalized - p2_normalized) / 2
        return avg_direction, harmony_strength, True
    else:
        # Opposite directions
        return 0, 0, False

def main():
    clock = pygame.time.Clock()
    running = True
    last_time = time.time()
    
    # Plant state
    plant_segments = []
    flowers = []
    harmony_particles = []
    
    # Growth parameters
    plant_base_x = SCREEN_WIDTH // 2
    plant_base_y = SCREEN_HEIGHT - 50 * SCALE_FACTOR
    current_angle = -90  # Start growing upward
    segment_length = 25 * SCALE_FACTOR
    
    # Game state
    growth_active = False
    harmony_level = 0.0
    background_pulse = 0.0
    last_growth_time = 0
    growth_cooldown = 0.3
    
    # Input states
    p1_button_pressed = False
    p2_button_pressed = False
    p1_switch_state = 0
    p2_switch_state = 1
    
    # Add initial root segment
    root_segment = PlantSegment(plant_base_x, plant_base_y, current_angle, segment_length)
    root_segment.growth_animation = 1.0
    plant_segments.append(root_segment)
    
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
        
        # Read serial input
        p1_joy_x, p2_joy_x = 2048, 2048  # Default neutral
        p1_button, p2_button = 1, 1      # Default unpressed
        p1_switch, p2_switch = 0, 1      # Default states
        
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
                            p1_switch = int(values[6])
                            p2_switch = int(values[7])
                except (ValueError, IndexError):
                    pass
        else:
            # Keyboard fallback for testing
            keys = pygame.key.get_pressed()
            if keys[pygame.K_a]: p1_joy_x = 0
            if keys[pygame.K_d]: p1_joy_x = 4095
            if keys[pygame.K_LEFT]: p2_joy_x = 0
            if keys[pygame.K_RIGHT]: p2_joy_x = 4095
            if keys[pygame.K_SPACE]: p1_button = 0
            if keys[pygame.K_RETURN]: p2_button = 0
            if keys[pygame.K_w]: p1_switch = 1
            if keys[pygame.K_UP]: p2_switch = 0
        
        # Calculate joystick harmony
        direction, harmony_strength, in_harmony = calculate_joystick_harmony(p1_joy_x, p2_joy_x)
        
        # Update harmony level smoothly
        target_harmony = harmony_strength if in_harmony else 0
        harmony_level += (target_harmony - harmony_level) * dt * 3
        
        # Check if both switches agree on growth
        growth_active = (p1_switch == 1 and p2_switch == 0)  # Both switches "up"
        
        # Handle flower planting
        if plant_segments:
            tip_segment = plant_segments[-1]
            tip_pos = tip_segment.end_pos
            
            if p1_button == 0 and not p1_button_pressed:
                color = random.choice(FLOWER_COLORS)
                flowers.append(Flower(tip_pos.x, tip_pos.y, color))
                # Add harmony particles
                for _ in range(5):
                    harmony_particles.append(HarmonyParticle(tip_pos.x, tip_pos.y))
                p1_button_pressed = True
            elif p1_button == 1:
                p1_button_pressed = False
                
            if p2_button == 0 and not p2_button_pressed:
                color = random.choice(FLOWER_COLORS)
                flowers.append(Flower(tip_pos.x, tip_pos.y, color))
                # Add harmony particles
                for _ in range(5):
                    harmony_particles.append(HarmonyParticle(tip_pos.x, tip_pos.y))
                p2_button_pressed = True
            elif p2_button == 1:
                p2_button_pressed = False
        
        # Grow plant
        if (growth_active and in_harmony and harmony_level > 0.3 and 
            current_time - last_growth_time > growth_cooldown and
            len(plant_segments) < 100):  # Limit plant size
            
            if plant_segments:
                last_segment = plant_segments[-1]
                
                # Adjust angle based on joystick direction
                angle_change = direction * 30  # Max 30 degree change
                current_angle += angle_change
                
                # Keep angle reasonable (don't grow straight down)
                current_angle = max(-160, min(-20, current_angle))
                
                # Create new segment
                new_segment = PlantSegment(
                    last_segment.end_pos.x,
                    last_segment.end_pos.y,
                    current_angle,
                    segment_length
                )
                plant_segments.append(new_segment)
                
                # Add growth particles
                for _ in range(3):
                    harmony_particles.append(HarmonyParticle(
                        last_segment.end_pos.x, last_segment.end_pos.y
                    ))
                
                last_growth_time = current_time
        
        # Update all objects
        for segment in plant_segments:
            segment.update(dt)
        
        for flower in flowers:
            flower.update(dt)
        
        harmony_particles = [p for p in harmony_particles if p.life > 0]
        for particle in harmony_particles:
            particle.update(dt)
        
        # Update background pulse
        background_pulse += dt
        
        # Render
        # Dynamic background based on harmony
        pulse_intensity = int(10 * harmony_level * (1 + math.sin(background_pulse * 2) * 0.3))
        bg_color = tuple(max(0, min(255, c + pulse_intensity)) for c in BACKGROUND_BASE)
        screen.fill(bg_color)
        
        # Draw plant segments
        for segment in plant_segments:
            segment.draw(screen)
        
        # Draw flowers
        for flower in flowers:
            flower.draw(screen)
        
        # Draw harmony particles
        for particle in harmony_particles:
            particle.draw(screen)
        
        # Draw harmony indicator (subtle glow around plant tip)
        if plant_segments and harmony_level > 0.1:
            tip = plant_segments[-1].end_pos
            glow_radius = int(30 * harmony_level * SCALE_FACTOR)
            glow_alpha = int(50 * harmony_level)
            
            glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            glow_color = (*BRIGHT_GREEN, glow_alpha)
            pygame.draw.circle(glow_surf, glow_color, (glow_radius, glow_radius), glow_radius)
            screen.blit(glow_surf, (tip.x - glow_radius, tip.y - glow_radius), 
                       special_flags=pygame.BLEND_ALPHA_SDL2)
        
        # Draw growth status indicators in corners
        status_radius = 10 * SCALE_FACTOR
        # Player 1 indicator (bottom left)
        p1_color = BRIGHT_GREEN if (p1_switch == 1) else (100, 100, 100)
        pygame.draw.circle(screen, p1_color, 
                         (int(30 * SCALE_FACTOR), int(SCREEN_HEIGHT - 30 * SCALE_FACTOR)), 
                         int(status_radius))
        
        # Player 2 indicator (bottom right)  
        p2_color = BRIGHT_GREEN if (p2_switch == 0) else (100, 100, 100)
        pygame.draw.circle(screen, p2_color, 
                         (int(SCREEN_WIDTH - 30 * SCALE_FACTOR), int(SCREEN_HEIGHT - 30 * SCALE_FACTOR)), 
                         int(status_radius))
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == '__main__':
    main()