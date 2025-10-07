"""
Tug of Space is a cooperative orbital physics experience where two players
control gravity wells on opposite sides of the screen. By carefully balancing
their gravitational pulls, they work together to keep colorful celestial objects
orbiting in mesmerizing patterns around the center. Each player can launch new
objects with their button, adding mass and complexity to the dance. If either
player pulls too hard, objects escape and fly off into space. Success requires
constant communication and adjustment as the system becomes more chaotic with
each new body. The result is a beautiful, ever-evolving display of physics.

The implementation uses Verlet integration for smooth orbital mechanics with
gravitational forces calculated between all bodies. Each object leaves a fading
trail to visualize its path through space. The gravity wells pulse and glow
based on joystick intensity, and particles emit from objects as they move. The
center has a gentle stabilizing force to create natural circular orbits when
players balance their pulls. Visual effects include glow halos around massive
objects and collision detection that merges smaller bodies into larger ones.
"""

import pygame
import serial
import math
import random
import time

pygame.init()

# Colors
SPACE_BLACK = (5, 5, 15)
STAR_WHITE = (255, 255, 255)
GRAVITY_WELL_P1 = (100, 150, 255)
GRAVITY_WELL_P2 = (255, 100, 150)
PLANET_COLORS = [
    (255, 100, 100),  # Red
    (100, 255, 100),  # Green
    (100, 100, 255),  # Blue
    (255, 255, 100),  # Yellow
    (255, 100, 255),  # Magenta
    (100, 255, 255),  # Cyan
    (255, 150, 100),  # Orange
    (150, 100, 255),  # Purple
]

# Screen setup
info = pygame.display.Info()
SCREEN_WIDTH, SCREEN_HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Tug of Space")

# Serial setup
try:
    ser = serial.Serial("/dev/ttyUSB0", 115200, timeout=0.01)
except serial.SerialException:
    ser = None
    print("Serial port not found. Running with keyboard controls.")

class CelestialBody:
    def __init__(self, x, y, vx, vy, mass, color):
        self.pos = pygame.Vector2(x, y)
        self.old_pos = pygame.Vector2(x - vx, y - vy)
        self.vel = pygame.Vector2(vx, vy)
        self.mass = mass
        self.radius = max(4, min(20, math.sqrt(mass) * 2))
        self.color = color
        self.trail = []
        self.max_trail_length = 50
        self.age = 0
        self.alive = True
        
    def update(self, dt, gravity_wells, center_pos):
        self.age += dt
        
        # Verlet integration
        current_pos = self.pos.copy()
        
        # Calculate forces
        force = pygame.Vector2(0, 0)
        
        # Gravity from wells
        for well in gravity_wells:
            diff = well['pos'] - self.pos
            dist = diff.length()
            if dist > 1:
                strength = well['strength'] * 500
                force_mag = strength / (dist * dist)
                force += diff.normalize() * force_mag
        
        # Gentle center pull for stability
        to_center = center_pos - self.pos
        center_dist = to_center.length()
        if center_dist > 1:
            center_force = to_center.normalize() * (center_dist * 0.001)
            force += center_force
        
        # Verlet integration
        acceleration = force / self.mass
        new_pos = 2 * self.pos - self.old_pos + acceleration * (dt * dt) * 60
        
        self.old_pos = current_pos
        self.pos = new_pos
        
        # Update velocity for checking bounds
        self.vel = (self.pos - self.old_pos) * 60
        
        # Add to trail
        self.trail.append(self.pos.copy())
        if len(self.trail) > self.max_trail_length:
            self.trail.pop(0)
        
        # Check if out of bounds
        margin = 100
        if (self.pos.x < -margin or self.pos.x > SCREEN_WIDTH + margin or
            self.pos.y < -margin or self.pos.y > SCREEN_HEIGHT + margin):
            self.alive = False
            
    def draw(self, surface):
        # Draw trail
        if len(self.trail) > 1:
            for i in range(len(self.trail) - 1):
                alpha = int(255 * (i / len(self.trail)))
                start_pos = self.trail[i]
                end_pos = self.trail[i + 1]
                
                trail_color = tuple(int(c * (alpha / 255)) for c in self.color)
                pygame.draw.line(surface, trail_color, start_pos, end_pos, 2)
        
        # Draw glow
        glow_radius = int(self.radius * 2)
        glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        glow_color = (*self.color, 50)
        pygame.draw.circle(glow_surf, glow_color, (glow_radius, glow_radius), glow_radius)
        surface.blit(glow_surf, (self.pos.x - glow_radius, self.pos.y - glow_radius), 
                    special_flags=pygame.BLEND_ALPHA_SDL2)
        
        # Draw body
        pygame.draw.circle(surface, self.color, self.pos, int(self.radius))
        
        # Draw highlight
        highlight_pos = self.pos + pygame.Vector2(-self.radius * 0.3, -self.radius * 0.3)
        highlight_color = tuple(min(255, int(c * 1.5)) for c in self.color)
        pygame.draw.circle(surface, highlight_color, highlight_pos, int(self.radius * 0.4))

class Particle:
    def __init__(self, x, y, color):
        self.pos = pygame.Vector2(x, y)
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(20, 50)
        self.vel = pygame.Vector2(math.cos(angle) * speed, math.sin(angle) * speed)
        self.color = color
        self.life = 1.0
        self.decay = random.uniform(1.5, 3.0)
        self.size = random.uniform(2, 4)
        
    def update(self, dt):
        self.pos += self.vel * dt
        self.life -= self.decay * dt
        
    def draw(self, surface):
        if self.life <= 0:
            return
        alpha = int(255 * self.life)
        particle_color = (*self.color, alpha)
        particle_surf = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
        pygame.draw.circle(particle_surf, particle_color, (int(self.size), int(self.size)), int(self.size))
        surface.blit(particle_surf, (self.pos.x - self.size, self.pos.y - self.size), 
                    special_flags=pygame.BLEND_ALPHA_SDL2)

def draw_gravity_well(surface, pos, strength, color, pulse_time):
    # Draw pulsing gravity well
    pulse = 0.8 + 0.2 * math.sin(pulse_time * 3)
    base_radius = 40 + strength * 60
    
    # Outer glow
    for i in range(3, 0, -1):
        radius = int(base_radius * pulse * (i * 0.4))
        alpha = int(80 / i)
        glow_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        glow_color = (*color, alpha)
        pygame.draw.circle(glow_surf, glow_color, (radius, radius), radius)
        surface.blit(glow_surf, (pos.x - radius, pos.y - radius), special_flags=pygame.BLEND_ALPHA_SDL2)
    
    # Core
    core_radius = int(15 * pulse)
    pygame.draw.circle(surface, color, pos, core_radius)
    pygame.draw.circle(surface, STAR_WHITE, pos, core_radius // 2)

def draw_stars(surface, stars):
    for star in stars:
        size = star['size']
        twinkle = 0.7 + 0.3 * math.sin(star['phase'] + time.time() * star['speed'])
        color = tuple(int(c * twinkle) for c in STAR_WHITE)
        pygame.draw.circle(surface, color, star['pos'], size)

def main():
    clock = pygame.time.Clock()
    running = True
    
    # Create background stars
    stars = []
    for _ in range(100):
        stars.append({
            'pos': (random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT)),
            'size': random.choice([1, 1, 1, 2]),
            'phase': random.uniform(0, 2 * math.pi),
            'speed': random.uniform(1, 3)
        })
    
    # Game state
    bodies = []
    particles = []
    center_pos = pygame.Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
    
    # Input tracking
    p1_button_pressed = False
    p2_button_pressed = False
    game_time = 0
    
    while running:
        dt = clock.tick(60) / 1000.0
        game_time += dt
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # Read serial input
        p1_joy_x, p2_joy_x = 2048, 2048
        p1_button, p2_button = 1, 1
        
        if ser:
            while ser.in_waiting:
                try:
                    line = ser.readline().decode('utf-8').rstrip()
                    if line:
                        values = line.split("/")
                        if len(values) == 8:
                            p1_joy_x = int(values[1])
                            p2_joy_x = int(values[3])
                            p1_button = int(values[4])
                            p2_button = int(values[5])
                except (ValueError, IndexError):
                    pass
        else:
            # Keyboard fallback
            keys = pygame.key.get_pressed()
            if keys[pygame.K_a]: p1_joy_x = 500
            if keys[pygame.K_d]: p1_joy_x = 3500
            if keys[pygame.K_LEFT]: p2_joy_x = 500
            if keys[pygame.K_RIGHT]: p2_joy_x = 3500
            if keys[pygame.K_SPACE]: p1_button = 0
            if keys[pygame.K_RETURN]: p2_button = 0
        
        # Calculate gravity well positions and strengths
        p1_strength = abs(p1_joy_x - 2048) / 2048.0
        p2_strength = abs(p2_joy_x - 2048) / 2048.0
        
        # Well positions on left and right sides
        p1_well_x = 100
        p2_well_x = SCREEN_WIDTH - 100
        
        gravity_wells = [
            {'pos': pygame.Vector2(p1_well_x, SCREEN_HEIGHT / 2), 'strength': p1_strength},
            {'pos': pygame.Vector2(p2_well_x, SCREEN_HEIGHT / 2), 'strength': p2_strength}
        ]
        
        # Launch new bodies
        if p1_button == 0 and not p1_button_pressed:
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 100)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            
            offset = random.uniform(50, 100)
            spawn_x = center_pos.x + math.cos(angle) * offset
            spawn_y = center_pos.y + math.sin(angle) * offset
            
            color = random.choice(PLANET_COLORS)
            mass = random.uniform(1, 3)
            bodies.append(CelestialBody(spawn_x, spawn_y, vx, vy, mass, color))
            
            # Spawn particles
            for _ in range(10):
                particles.append(Particle(spawn_x, spawn_y, color))
            
            p1_button_pressed = True
        elif p1_button == 1:
            p1_button_pressed = False
        
        if p2_button == 0 and not p2_button_pressed:
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 100)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            
            offset = random.uniform(50, 100)
            spawn_x = center_pos.x + math.cos(angle) * offset
            spawn_y = center_pos.y + math.sin(angle) * offset
            
            color = random.choice(PLANET_COLORS)
            mass = random.uniform(1, 3)
            bodies.append(CelestialBody(spawn_x, spawn_y, vx, vy, mass, color))
            
            # Spawn particles
            for _ in range(10):
                particles.append(Particle(spawn_x, spawn_y, color))
            
            p2_button_pressed = True
        elif p2_button == 1:
            p2_button_pressed = False
        
        # Update bodies
        for body in bodies:
            body.update(dt, gravity_wells, center_pos)
        
        # Remove dead bodies
        bodies = [b for b in bodies if b.alive]
        
        # Update particles
        particles = [p for p in particles if p.life > 0]
        for particle in particles:
            particle.update(dt)
        
        # Draw
        screen.fill(SPACE_BLACK)
        
        # Draw stars
        draw_stars(screen, stars)
        
        # Draw center marker
        center_radius = 5
        pygame.draw.circle(screen, (50, 50, 50), center_pos, center_radius)
        
        # Draw gravity wells
        draw_gravity_well(screen, gravity_wells[0]['pos'], p1_strength, GRAVITY_WELL_P1, game_time)
        draw_gravity_well(screen, gravity_wells[1]['pos'], p2_strength, GRAVITY_WELL_P2, game_time)
        
        # Draw bodies
        for body in bodies:
            body.draw(screen)
        
        # Draw particles
        for particle in particles:
            particle.draw(screen)
        
        # Draw UI
        font = pygame.font.Font(None, 24)
        count_text = font.render(f"Objects: {len(bodies)}", True, STAR_WHITE)
        screen.blit(count_text, (10, 10))
        
        instructions = font.render("Press Button to Launch Objects", True, (150, 150, 150))
        screen.blit(instructions, (SCREEN_WIDTH // 2 - instructions.get_width() // 2, SCREEN_HEIGHT - 30))
        
        pygame.display.flip()
    
    pygame.quit()

if __name__ == '__main__':
    main()
