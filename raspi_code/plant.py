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
    def __init__(self, x, y, angle, length, base_thickness=None):
        self.start_pos = pygame.Vector2(x, y)
        self.angle = angle
        self.length = length
        self.end_pos = self.start_pos + pygame.Vector2(
            math.cos(math.radians(angle)) * length,
            math.sin(math.radians(angle)) * length
        )
        self.base_thickness = base_thickness if base_thickness else 8 * SCALE_FACTOR
        self.thickness = self.base_thickness
        self.age = 0
        self.growth_animation = 0
        self.segment_index = 0
        
    def update(self, dt):
        self.age += dt
        if self.growth_animation < 1.0:
            self.growth_animation = min(1.0, self.growth_animation + dt * 2)
            
    def update_thickness(self, total_segments):
        # Older segments (lower index) get thicker as plant grows
        age_factor = max(0.5, 1.0 - (self.segment_index / max(1, total_segments)))
        thickness_boost = (total_segments - self.segment_index) * 0.5 * SCALE_FACTOR
        self.thickness = self.base_thickness + thickness_boost * age_factor
            
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

class Bud:
    def __init__(self, x, y, segment_index):
        self.pos = pygame.Vector2(x, y)
        self.segment_index = segment_index
        self.size = 0
        self.max_size = 8 * SCALE_FACTOR
        self.growth_speed = 4
        self.age = 0
        self.used = False
        self.pulse_offset = random.uniform(0, math.pi * 2)
        
    def update(self, dt):
        self.age += dt
        if self.size < self.max_size and not self.used:
            self.size = min(self.max_size, self.size + self.growth_speed * dt)
            
    def draw(self, surface):
        if self.size <= 0:
            return
            
        # Pulsing green bud
        pulse = 0.8 + 0.2 * math.sin(self.age * 3 + self.pulse_offset)
        if self.used:
            pulse *= 0.3  # Dim when used
            
        bud_color = tuple(int(c * pulse) for c in BRIGHT_GREEN)
        pygame.draw.circle(surface, bud_color, self.pos, int(self.size))
        
        # Small highlight
        highlight_pos = self.pos + pygame.Vector2(-2, -2)
        highlight_color = tuple(min(255, int(c * 1.5)) for c in bud_color)
        pygame.draw.circle(surface, highlight_color, highlight_pos, int(self.size * 0.4))

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

def calculate_joystick_direction_and_speed(p1_x, p2_x):
    """Calculate growth direction and speed from average joystick input"""
    # Convert to -1 to 1 range
    p1_normalized = (p1_x - 2048) / 2048.0
    p2_normalized = (p2_x - 2048) / 2048.0
    
    # Calculate average direction
    avg_direction = (p1_normalized + p2_normalized) / 2
    
    # Speed based on magnitude of average direction
    speed = abs(avg_direction)
    
    # Direction in degrees (convert from -1,1 to angle change)
    angle_change = avg_direction * 45  # Max 45 degrees per growth step
    
    return angle_change, speed

def main():
    clock = pygame.time.Clock()
    running = True
    last_time = time.time()
    
    # Plant state
    plant_segments = []
    flowers = []
    buds = []
    harmony_particles = []
    current_growth_point = None  # Tracks where we're currently growing from
    
    # Growth parameters
    plant_base_x = SCREEN_WIDTH // 2
    plant_base_y = SCREEN_HEIGHT - 50 * SCALE_FACTOR
    current_angle = -90  # Start growing upward
    segment_length = 25 * SCALE_FACTOR
    
    # Game state
    growth_active = False
    background_pulse = 0.0
    last_growth_time = 0
    growth_cooldown = 0.3  # Base growth speed
    
    # Input states
    p1_button_pressed = False
    p2_button_pressed = False
    p1_switch_state = 0
    p2_switch_state = 1
    
    # Add initial root segment
    root_segment = PlantSegment(plant_base_x, plant_base_y, current_angle, segment_length)
    root_segment.growth_animation = 1.0
    root_segment.segment_index = 0
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
            # Switch logic for keyboard: W and UP keys act as switches
            p1_switch = 1 if keys[pygame.K_w] else 0
            p2_switch = 0 if keys[pygame.K_UP] else 1
        
        # Calculate joystick direction and speed from average
        angle_change, growth_speed = calculate_joystick_direction_and_speed(p1_joy_x, p2_joy_x)
        

        
        # Check if both switches agree to GROW (both players must agree)
        if ser:
            # Hardware: both switches must be "up" to grow
            growth_active = (p1_switch == 1 and p2_switch == 0)
        else:
            # Keyboard: both keys must be pressed to grow (W + UP)
            keys = pygame.key.get_pressed()
            growth_active = keys[pygame.K_w] and keys[pygame.K_UP]
        
        # Handle differentiated button functions
        if plant_segments:
            tip_segment = plant_segments[-1]
            tip_pos = tip_segment.end_pos
            
            # Player 1: Plant flowers
            if p1_button == 0 and not p1_button_pressed:
                color = random.choice(FLOWER_COLORS)
                flowers.append(Flower(tip_pos.x, tip_pos.y, color))
                # Add harmony particles
                for _ in range(5):
                    harmony_particles.append(HarmonyParticle(tip_pos.x, tip_pos.y))
                p1_button_pressed = True
            elif p1_button == 1:
                p1_button_pressed = False
                
            # Player 2: Create buds (new growth points)
            if p2_button == 0 and not p2_button_pressed:
                # Place bud at current tip location, but it will become a branch point
                bud = Bud(tip_pos.x, tip_pos.y, len(plant_segments) - 1)
                buds.append(bud)
                # Add harmony particles
                for _ in range(3):
                    harmony_particles.append(HarmonyParticle(tip_pos.x, tip_pos.y))
                p2_button_pressed = True
            elif p2_button == 1:
                p2_button_pressed = False
        
        # Grow plant based on joystick average and switch agreement
        # Growth speed depends on joystick magnitude
        actual_cooldown = growth_cooldown / max(0.1, growth_speed)  # Faster with more joystick input
        
        if (growth_active and current_time - last_growth_time > actual_cooldown and len(plant_segments) < 200):
            
            if current_growth_point:
                # Apply joystick direction change
                test_angle = current_angle + angle_change
                test_angle = max(-160, min(160, test_angle))
                
                # Calculate where the next segment would end up
                next_end_x = current_growth_point.end_pos.x + math.cos(math.radians(test_angle)) * segment_length
                next_end_y = current_growth_point.end_pos.y + math.sin(math.radians(test_angle)) * segment_length
                
                # Check if next segment would go out of bounds
                margin = 80
                would_hit_edge = (next_end_x < margin or next_end_x > SCREEN_WIDTH - margin or 
                                 next_end_y < margin or next_end_y > SCREEN_HEIGHT - margin)
                
                if would_hit_edge and buds:
                    # Only branch if buds are available AND we would hit edge
                    next_bud = None
                    for bud in buds:
                        if not bud.used:
                            next_bud = bud
                            break
                    
                    if next_bud:
                        # Switch to growing from this bud
                        next_bud.used = True
                        current_growth_point = plant_segments[next_bud.segment_index]
                        current_angle = -45  # Start new branch
                        
                        # Create connecting segment from bud
                        new_segment = PlantSegment(
                            next_bud.pos.x,
                            next_bud.pos.y,
                            current_angle,
                            segment_length,
                            base_thickness=6 * SCALE_FACTOR
                        )
                        new_segment.segment_index = len(plant_segments)
                        plant_segments.append(new_segment)
                        current_growth_point = new_segment
                        
                        # Add growth particles
                        for _ in range(5):
                            harmony_particles.append(HarmonyParticle(next_bud.pos.x, next_bud.pos.y))
                        
                        last_growth_time = current_time
                elif not would_hit_edge:
                    # Normal growth - ALWAYS allow if not hitting edge (regardless of buds)
                    current_angle = test_angle
                    
                    # Create new segment
                    new_segment = PlantSegment(
                        current_growth_point.end_pos.x,
                        current_growth_point.end_pos.y,
                        current_angle,
                        segment_length
                    )
                    new_segment.segment_index = len(plant_segments)
                    plant_segments.append(new_segment)
                    current_growth_point = new_segment
                    
                    # Add growth particles
                    for _ in range(3):
                        harmony_particles.append(HarmonyParticle(
                            current_growth_point.end_pos.x, current_growth_point.end_pos.y
                        ))
                    
                    last_growth_time = current_time
                # If would hit edge but no buds available, just stop growing naturally
        
        # Update all objects
        for i, segment in enumerate(plant_segments):
            segment.update(dt)
            segment.update_thickness(len(plant_segments))
        
        for flower in flowers:
            flower.update(dt)
            
        for bud in buds:
            bud.update(dt)
        
        harmony_particles = [p for p in harmony_particles if p.life > 0]
        for particle in harmony_particles:
            particle.update(dt)
        
        # Update background pulse
        background_pulse += dt
        
        # Render
        # Dynamic background based on growth activity
        pulse_intensity = int(10 * growth_speed * (1 + math.sin(background_pulse * 2) * 0.3)) if growth_active else 0
        bg_color = tuple(max(0, min(255, c + pulse_intensity)) for c in BACKGROUND_BASE)
        screen.fill(bg_color)
        
        # Draw plant segments
        for segment in plant_segments:
            segment.draw(screen)
        
        # Draw flowers
        for flower in flowers:
            flower.draw(screen)
            
        # Draw buds
        for bud in buds:
            bud.draw(screen)
        
        # Draw harmony particles
        for particle in harmony_particles:
            particle.draw(screen)
        
        # Draw growth indicator (subtle glow around current growth point)
        if current_growth_point and growth_active and growth_speed > 0.1:
            tip = current_growth_point.end_pos
            glow_radius = int(30 * growth_speed * SCALE_FACTOR)
            glow_alpha = int(50 * growth_speed)
            
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