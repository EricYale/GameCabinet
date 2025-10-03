# This game is a cooperative digital terrarium called "Symbiosis: The Living Plant" where
# two players nurture and evolve a single shared organism through coordinated actions.
# Unlike traditional games with winners and losers, this is an interactive living sculpture
# that grows uniquely based on player cooperation, rhythm, and environmental management.
# Each session produces a different plant shaped by how the players interact together.

# The gameplay involves complementary roles where Player 1 controls growth direction and
# Player 2 manages growth speed and resource focus. Coordinated movements create healthy
# balanced growth while conflicting inputs cause chaos. Environmental switches control
# macro conditions like water/land and light/dark cycles, while timed button presses
# trigger special growth events like blooming, branching, or evolutionary mutations when
# pressed simultaneously. The plant's visual form, complexity, and behavior reflect the
# players' cooperation style, creating a unique living artwork each time.

import pygame
import serial
import math
import random
import time

pygame.init()

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BROWN = (139, 69, 19)
YELLOW = (255, 255, 0)
PINK = (255, 192, 203)
BLUE = (0, 100, 255)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
DARK_GREEN = (0, 100, 0)

info = pygame.display.Info()
SCREEN_WIDTH, SCREEN_HEIGHT = info.current_w, info.current_h
SCALE_FACTOR = min(SCREEN_WIDTH / 1280.0, 1.0)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Symbiosis: The Living Plant")
font = pygame.font.Font(None, int(48 * SCALE_FACTOR))
small_font = pygame.font.Font(None, int(24 * SCALE_FACTOR))

try:
    ser = serial.Serial("/dev/ttyUSB0", 115200, timeout=0.01)
except serial.SerialException:
    ser = None
    print("Serial port not found. Running with keyboard controls.")

class PlantSegment:
    def __init__(self, x, y, parent=None, segment_type="stem"):
        self.x = x
        self.y = y
        self.parent = parent
        self.children = []
        self.age = 0
        self.thickness = 2 * SCALE_FACTOR
        self.color = [0, 255, 0]
        self.segment_type = segment_type
        self.health = 1.0
        self.growth_direction = 0
        self.length = 10 * SCALE_FACTOR
        self.has_flower = False
        self.flower_color = [255, 192, 203]
        self.glow = 0
        self.mutation_traits = []
        
    def update(self, dt, environment):
        self.age += dt
        
        if self.segment_type == "root":
            self.color = [139, 69, 19]
            if environment["water_mode"]:
                self.health = min(1.0, self.health + dt * 0.1)
        elif self.segment_type == "stem":
            if environment["light_mode"]:
                self.health = min(1.0, self.health + dt * 0.05)
        
        if environment["storm_mode"]:
            self.health -= dt * 0.02
        
        self.health = max(0.1, self.health)
        
        if "bioluminescent" in self.mutation_traits:
            self.glow = 0.5 + 0.3 * math.sin(time.time() * 3)
        
        for child in self.children:
            child.update(dt, environment)
    
    def draw(self, surface):
        if self.parent:
            thickness = max(1, int(self.thickness * self.health))
            
            if self.glow > 0:
                for i in range(3):
                    glow_color = [min(255, c + int(self.glow * 100)) for c in self.color]
                    pygame.draw.line(surface, glow_color, 
                                   (self.parent.x, self.parent.y), 
                                   (self.x, self.y), thickness + i * 2)
            
            pygame.draw.line(surface, self.color, 
                           (self.parent.x, self.parent.y), 
                           (self.x, self.y), thickness)
        
        if self.has_flower:
            flower_size = int(5 * SCALE_FACTOR * self.health)
            pygame.draw.circle(surface, self.flower_color, 
                             (int(self.x), int(self.y)), flower_size)
            pygame.draw.circle(surface, YELLOW, 
                             (int(self.x), int(self.y)), flower_size // 2)
        
        for child in self.children:
            child.draw(surface)

class Plant:
    def __init__(self, start_x, start_y):
        self.root = PlantSegment(start_x, start_y)
        self.segments = [self.root]
        self.energy = 50
        self.cooperation_level = 0.5
        self.growth_events = []
        self.mutations = []
        self.total_segments = 1
        
    def grow(self, direction_x, direction_y, speed, environment):
        if self.energy < 5:
            return
            
        growth_candidates = [s for s in self.segments if len(s.children) < 3]
        if not growth_candidates:
            return
            
        parent = random.choice(growth_candidates)
        
        base_length = 15 * SCALE_FACTOR * speed
        if environment["storm_mode"]:
            base_length *= 1.5
        
        new_x = parent.x + direction_x * base_length
        new_y = parent.y + direction_y * base_length
        
        segment_type = "root" if direction_y > 0.5 else "stem"
        new_segment = PlantSegment(new_x, new_y, parent, segment_type)
        
        new_segment.thickness = max(1, parent.thickness * (0.8 + speed * 0.4))
        
        if environment["light_mode"] and segment_type == "stem":
            new_segment.color = [0, 255, 0]
        elif environment["water_mode"] and segment_type == "root":
            new_segment.color = [139, 69, 19]
        else:
            new_segment.color = [0, 100, 0]
            
        parent.children.append(new_segment)
        self.segments.append(new_segment)
        self.total_segments += 1
        self.energy -= 3
        
    def trigger_bloom(self, environment):
        if self.energy < 10:
            return False
            
        stem_segments = [s for s in self.segments if s.segment_type == "stem" and not s.has_flower]
        if not stem_segments:
            return False
            
        bloom_segment = random.choice(stem_segments)
        bloom_segment.has_flower = True
        
        if environment["light_mode"]:
            bloom_segment.flower_color = [255, 255, 0]
        else:
            bloom_segment.flower_color = [128, 0, 128]
            
        self.energy -= 8
        return True
        
    def trigger_branch(self):
        if self.energy < 15:
            return False
            
        branch_candidates = [s for s in self.segments if len(s.children) < 2 and s.age > 2]
        if not branch_candidates:
            return False
            
        parent = random.choice(branch_candidates)
        
        angle1 = random.uniform(-math.pi/3, math.pi/3)
        angle2 = angle1 + random.uniform(math.pi/4, math.pi/2)
        
        for angle in [angle1, angle2]:
            length = 12 * SCALE_FACTOR
            new_x = parent.x + math.cos(angle) * length
            new_y = parent.y + math.sin(angle) * length
            
            new_segment = PlantSegment(new_x, new_y, parent)
            new_segment.thickness = parent.thickness * 0.7
            parent.children.append(new_segment)
            self.segments.append(new_segment)
            
        self.total_segments += 2
        self.energy -= 12
        return True
        
    def trigger_mutation(self, environment):
        if len(self.mutations) >= 3:
            return False
            
        mutation_types = ["bioluminescent", "fractal_branching", "color_shift", "gigantism"]
        mutation = random.choice(mutation_types)
        
        if mutation == "bioluminescent":
            for segment in random.sample(self.segments, min(5, len(self.segments))):
                segment.mutation_traits.append("bioluminescent")
                
        elif mutation == "color_shift":
            new_colors = [[128, 0, 128], [255, 165, 0], [0, 100, 255], [255, 192, 203]]
            new_color = random.choice(new_colors)
            for segment in self.segments:
                if segment.segment_type == "stem":
                    segment.color = new_color[:]
                    
        elif mutation == "gigantism":
            for segment in self.segments:
                segment.thickness *= 1.5
                
        self.mutations.append(mutation)
        return True
        
    def shed_leaves(self):
        dead_segments = [s for s in self.segments if s.health < 0.3 and len(s.children) == 0]
        for segment in dead_segments:
            if segment.parent:
                segment.parent.children.remove(segment)
                self.segments.remove(segment)
                self.energy += 2
                
    def update(self, dt, environment, cooperation):
        self.cooperation_level = cooperation
        self.energy = min(100, self.energy + dt * (1 + cooperation))
        
        if environment["storm_mode"]:
            self.energy -= dt * 2
            
        for segment in self.segments:
            segment.update(dt, environment)
            
    def draw(self, surface):
        self.root.draw(surface)

def calculate_cooperation(p1_joy_x, p1_joy_y, p2_joy_x, p2_joy_y):
    p1_magnitude = math.sqrt(p1_joy_x**2 + p1_joy_y**2)
    p2_magnitude = math.sqrt(p2_joy_x**2 + p2_joy_y**2)
    
    if p1_magnitude < 0.1 or p2_magnitude < 0.1:
        return 0.5
        
    similarity = 1.0 - abs(p1_magnitude - p2_magnitude)
    direction_diff = abs(math.atan2(p1_joy_y, p1_joy_x) - math.atan2(p2_joy_y, p2_joy_x))
    direction_sync = 1.0 - min(direction_diff, 2*math.pi - direction_diff) / math.pi
    
    return (similarity + direction_sync) / 2

def draw_environment_info(surface, environment, plant):
    info_y = 30 * SCALE_FACTOR
    
    env_text = f"Environment: {'Water' if environment['water_mode'] else 'Land'} | "
    env_text += f"{'Light' if environment['light_mode'] else 'Dark'} | "
    env_text += f"{'Storm' if environment['storm_mode'] else 'Calm'}"
    
    env_surface = small_font.render(env_text, True, WHITE)
    surface.blit(env_surface, (30 * SCALE_FACTOR, info_y))
    
    stats_text = f"Energy: {int(plant.energy)} | Segments: {plant.total_segments} | Mutations: {len(plant.mutations)}"
    stats_surface = small_font.render(stats_text, True, WHITE)
    surface.blit(stats_surface, (30 * SCALE_FACTOR, info_y + 25 * SCALE_FACTOR))
    
    coop_bar_width = 200 * SCALE_FACTOR
    coop_bar_height = 10 * SCALE_FACTOR
    coop_x = SCREEN_WIDTH - coop_bar_width - 30 * SCALE_FACTOR
    coop_y = info_y
    
    pygame.draw.rect(surface, WHITE, (coop_x, coop_y, coop_bar_width, coop_bar_height), 1)
    coop_fill = plant.cooperation_level * coop_bar_width
    coop_color = GREEN if plant.cooperation_level > 0.7 else YELLOW if plant.cooperation_level > 0.4 else ORANGE
    pygame.draw.rect(surface, coop_color, (coop_x, coop_y, coop_fill, coop_bar_height))
    
    coop_text = f"Cooperation: {plant.cooperation_level:.1%}"
    coop_surface = small_font.render(coop_text, True, WHITE)
    surface.blit(coop_surface, (coop_x, coop_y + 15 * SCALE_FACTOR))

def main():
    clock = pygame.time.Clock()
    running = True
    
    plant = Plant(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100 * SCALE_FACTOR)
    
    environment = {
        "water_mode": False,
        "light_mode": True,
        "storm_mode": False
    }
    
    p1_button_pressed = False
    p2_button_pressed = False
    last_sync_press = 0
    
    growth_timer = 0
    
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
            p1_joy_x = -0.7 if keys[pygame.K_a] else (0.7 if keys[pygame.K_d] else 0)
            p1_joy_y = -0.7 if keys[pygame.K_w] else (0.7 if keys[pygame.K_s] else 0)
            p2_joy_x = -0.7 if keys[pygame.K_LEFT] else (0.7 if keys[pygame.K_RIGHT] else 0)
            p2_joy_y = -0.7 if keys[pygame.K_UP] else (0.7 if keys[pygame.K_DOWN] else 0)
            p1_button = 0 if keys[pygame.K_SPACE] else 1
            p2_button = 0 if keys[pygame.K_RETURN] else 1
            p1_switch = 1 if keys[pygame.K_q] else 0
            p2_switch = 0 if keys[pygame.K_e] else 1
            
        cooperation = calculate_cooperation(p1_joy_x, p1_joy_y, p2_joy_x, p2_joy_y)
        
        environment["water_mode"] = (p1_switch == 0)
        environment["light_mode"] = (p2_switch == 0)
        environment["storm_mode"] = (p1_switch == 1 and p2_switch == 1)
        
        growth_timer += dt
        if growth_timer > 0.3:
            direction_x = p1_joy_x
            direction_y = p1_joy_y
            speed = max(0.1, math.sqrt(p2_joy_x**2 + p2_joy_y**2))
            
            if abs(direction_x) > 0.1 or abs(direction_y) > 0.1:
                plant.grow(direction_x, -direction_y, speed, environment)
            growth_timer = 0
            
        p1_button_now = (p1_button == 0 and not p1_button_pressed)
        p2_button_now = (p2_button == 0 and not p2_button_pressed)
        p1_button_pressed = (p1_button == 0)
        p2_button_pressed = (p2_button == 0)
        
        if p1_button_now and p2_button_now:
            if current_time - last_sync_press > 2.0:
                plant.trigger_mutation(environment)
                last_sync_press = current_time
        elif p1_button_now:
            if environment["light_mode"]:
                plant.trigger_bloom(environment)
            else:
                plant.shed_leaves()
        elif p2_button_now:
            plant.trigger_branch()
            
        plant.update(dt, environment, cooperation)
        
        screen.fill(BLACK)
        
        ground_y = SCREEN_HEIGHT - 50 * SCALE_FACTOR
        pygame.draw.line(screen, BROWN, (0, ground_y), (SCREEN_WIDTH, ground_y), 3)
        
        plant.draw(screen)
        draw_environment_info(screen, environment, plant)
        
        if len(plant.mutations) > 0:
            mutation_text = f"Mutations: {', '.join(plant.mutations)}"
            mut_surface = small_font.render(mutation_text, True, PURPLE)
            screen.blit(mut_surface, (30 * SCALE_FACTOR, SCREEN_HEIGHT - 30 * SCALE_FACTOR))
            
        pygame.display.flip()
        clock.tick(60)
        
    pygame.quit()

if __name__ == '__main__':
    main()