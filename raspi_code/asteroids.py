
# This game is a two-player version of the classic arcade game "Asteroids,"
# designed for a custom-built mini arcade cabinet. Two players control their
# respective ships on a single screen, viewed from opposite sides. The objective
# is to survive as long as possible by shooting asteroids and the opponent's
# ship. Each player has a joystick for rotation, a button for shooting, and a
# toggle switch to control acceleration. The game uses simple vector graphics
# to represent ships, asteroids, and bullets, staying true to the original's
# aesthetic and ensuring the display is clear for both players regardless of
# their orientation.

# The game is implemented in Python using the Pygame library for graphics and
# event handling. It reads player inputs from an ESP32 microcontroller via a
# serial connection. The serial data, a slash-delimited string of sensor
# values, is parsed to control each player's ship. The game features wrap-around
# screen space, so objects leaving one edge of the screen reappear on the
# opposite side. Player lives are displayed as dots on the left and right edges
# of the screen. The game state, including positions and velocities of all
# objects, is updated in a main loop that also handles rendering and input
# processing. All motion is made framerate-independent through the use of
# a delta-time (dt) value in physics calculations.

import pygame
import serial
import math
import random
import time

pygame.init()

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

info = pygame.display.Info()
SCREEN_WIDTH, SCREEN_HEIGHT = info.current_w, info.current_h
SCALE_FACTOR = min(SCREEN_WIDTH / 1280.0, 1.0) # Cap at 1.0 for screens larger than reference
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Asteroids")
font = pygame.font.Font(None, int(74 * SCALE_FACTOR))
small_font = pygame.font.Font(None, int(50 * SCALE_FACTOR))

try:
    ser = serial.Serial("/dev/ttyUSB0", 115200, timeout=0.01)
except serial.SerialException:
    ser = None
    print("Serial port not found. Running with keyboard controls.")

class Ship:
    def __init__(self, x, y, color, player_id):
        self.player_id = player_id
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)
        self.angle = 0
        self.color = color
        self.radius = 20 * SCALE_FACTOR
        self.lives = 5
        self.is_accelerating = False
        self.turn_direction = 0
        self.last_shot_time = 0
        self.shoot_cooldown = 0.25
        self.respawn_time = 0
        self.invincible = False
        self.acceleration_rate = 200 * SCALE_FACTOR
        self.turn_rate = 150
        self.damping = 0.5

    def draw(self, surface):
        if self.lives <= 0 or self.is_respawning():
            return

        if self.invincible and (pygame.time.get_ticks() // 200) % 2 == 0:
            return

        draw_radius = 30 * SCALE_FACTOR
        point1 = self.pos + pygame.Vector2(math.cos(math.radians(self.angle)), math.sin(math.radians(self.angle))) * draw_radius
        point2 = self.pos + pygame.Vector2(math.cos(math.radians(self.angle + 140)), math.sin(math.radians(self.angle + 140))) * draw_radius
        point3 = self.pos + pygame.Vector2(math.cos(math.radians(self.angle - 140)), math.sin(math.radians(self.angle - 140))) * draw_radius
        pygame.draw.polygon(surface, self.color, [point1, point2, point3], 2)

    def update(self, dt):
        self.angle += self.turn_direction * self.turn_rate * dt

        if self.is_accelerating:
            acceleration = pygame.Vector2(math.cos(math.radians(self.angle)), math.sin(math.radians(self.angle))) * self.acceleration_rate
            self.vel += acceleration * dt
        
        self.vel -= self.vel * self.damping * dt
        self.pos += self.vel * dt

        self.pos.x %= SCREEN_WIDTH
        self.pos.y %= SCREEN_HEIGHT

        if self.invincible and pygame.time.get_ticks() > self.respawn_time + 3000:
            self.invincible = False

        if self.is_respawning():
            self.vel = pygame.Vector2(0, 0)

    def shoot(self, bullets):
        current_time = time.time()
        if self.lives > 0 and not self.is_respawning() and current_time - self.last_shot_time > self.shoot_cooldown:
            self.last_shot_time = current_time
            bullet_vel = self.vel + pygame.Vector2(math.cos(math.radians(self.angle)), math.sin(math.radians(self.angle))) * 300 * SCALE_FACTOR
            bullets.append(Bullet(self.pos, bullet_vel, self.player_id))

    def hit(self):
        if not self.invincible:
            self.lives -= 1
            if self.lives > 0:
                self.respawn()
            return True
        return False

    def respawn(self):
        self.pos = pygame.Vector2(SCREEN_WIDTH // 4 if self.player_id == 1 else 3 * SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2)
        self.vel = pygame.Vector2(0, 0)
        self.angle = 0
        self.respawn_time = pygame.time.get_ticks()
        self.invincible = True

    def is_respawning(self):
        return self.invincible and pygame.time.get_ticks() < self.respawn_time + 3000

class Bullet:
    def __init__(self, pos, vel, owner_id):
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(vel)
        self.radius = 3 * SCALE_FACTOR
        self.lifespan = 2.5
        self.birth_time = time.time()
        self.owner_id = owner_id

    def draw(self, surface):
        pygame.draw.circle(surface, WHITE, self.pos, self.radius)

    def update(self, dt):
        self.pos += self.vel * dt
        self.pos.x %= SCREEN_WIDTH
        self.pos.y %= SCREEN_HEIGHT

class Asteroid:
    def __init__(self, pos, size):
        self.pos = pygame.Vector2(pos)
        max_vel = 100 * SCALE_FACTOR
        self.vel = pygame.Vector2(random.uniform(-max_vel, max_vel), random.uniform(-max_vel, max_vel))
        if self.vel.length() == 0:
            self.vel = pygame.Vector2(50 * SCALE_FACTOR, 50 * SCALE_FACTOR)
        self.size = size
        self.radius = size * 10 * SCALE_FACTOR
        self.angle = 0
        self.rotation_speed = random.uniform(-60, 60)
        self.shape = []
        num_vertices = random.randint(7, 12)
        for i in range(num_vertices):
            angle = (i / num_vertices) * 2 * math.pi
            radius = self.radius + random.uniform(-self.radius/4, self.radius/4)
            self.shape.append(pygame.Vector2(radius * math.cos(angle), radius * math.sin(angle)))

    def draw(self, surface):
        points = []
        for point in self.shape:
            rotated_point = point.rotate(self.angle)
            points.append(self.pos + rotated_point)
        pygame.draw.polygon(surface, WHITE, points, 2)

    def update(self, dt):
        self.pos += self.vel * dt
        self.angle += self.rotation_speed * dt
        self.pos.x %= SCREEN_WIDTH
        self.pos.y %= SCREEN_HEIGHT

def spawn_asteroid(size, players):
    while True:
        edge = random.choice(['top', 'bottom', 'left', 'right'])
        spawn_buffer = 30 * SCALE_FACTOR
        if edge == 'top':
            pos = pygame.Vector2(random.uniform(0, SCREEN_WIDTH), -spawn_buffer)
        elif edge == 'bottom':
            pos = pygame.Vector2(random.uniform(0, SCREEN_WIDTH), SCREEN_HEIGHT + spawn_buffer)
        elif edge == 'left':
            pos = pygame.Vector2(-spawn_buffer, random.uniform(0, SCREEN_HEIGHT))
        else: # right
            pos = pygame.Vector2(SCREEN_WIDTH + spawn_buffer, random.uniform(0, SCREEN_HEIGHT))
        
        too_close = False
        for player in players:
            if pos.distance_to(player.pos) < 200 * SCALE_FACTOR:
                too_close = True
                break
        if not too_close:
            return Asteroid(pos, size)

def draw_lives(surface, player, side):
    life_radius = 5 * SCALE_FACTOR
    if side == 'left':
        x_pos = 30 * SCALE_FACTOR
        for i in range(player.lives):
            pygame.draw.circle(surface, player.color, (x_pos, 40 * SCALE_FACTOR + i * 20 * SCALE_FACTOR), life_radius)
    else:
        x_pos = SCREEN_WIDTH - 30 * SCALE_FACTOR
        for i in range(player.lives):
            pygame.draw.circle(surface, player.color, (x_pos, 40 * SCALE_FACTOR + i * 20 * SCALE_FACTOR), life_radius)

def main():
    clock = pygame.time.Clock()
    running = True

    player1 = Ship(SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2, BLUE, 1)
    player2 = Ship(3 * SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2, RED, 2)
    players = [player1, player2]

    bullets = []
    asteroids = []
    num_asteroids = max(3, int(8 * SCALE_FACTOR))
    for _ in range(num_asteroids):
        asteroids.append(spawn_asteroid(3, players))

    p1_button_pressed = False
    p2_button_pressed = False
    
    p1_switch_state = 0
    p2_switch_state = 1

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

        player1.turn_direction = 0
        player2.turn_direction = 0

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

                            if p1_joy_x < 1024: player1.turn_direction = -1
                            if p1_joy_x > 3072: player1.turn_direction = 1
                            
                            if p2_joy_x < 1024: player2.turn_direction = 1
                            if p2_joy_x > 3072: player2.turn_direction = -1

                            if p1_button == 0 and not p1_button_pressed:
                                player1.shoot(bullets)
                                p1_button_pressed = True
                            elif p1_button == 1:
                                p1_button_pressed = False

                            if p2_button == 0 and not p2_button_pressed:
                                player2.shoot(bullets)
                                p2_button_pressed = True
                            elif p2_button == 1:
                                p2_button_pressed = False
                            
                            if p1_switch != p1_switch_state:
                                player1.is_accelerating = not player1.is_accelerating
                                p1_switch_state = p1_switch

                            if p2_switch != p2_switch_state:
                                player2.is_accelerating = not player2.is_accelerating
                                p2_switch_state = p2_switch

                except (ValueError, IndexError):
                    pass
        else:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_a]: player1.turn_direction = -1
            if keys[pygame.K_d]: player1.turn_direction = 1
            player1.is_accelerating = keys[pygame.K_w]
            if keys[pygame.K_SPACE]: player1.shoot(bullets)

            if keys[pygame.K_LEFT]: player2.turn_direction = -1
            if keys[pygame.K_RIGHT]: player2.turn_direction = 1
            player2.is_accelerating = keys[pygame.K_UP]
            if keys[pygame.K_RETURN]: player2.shoot(bullets)

        for obj in players + bullets + asteroids:
            obj.update(dt)

        active_bullets = [b for b in bullets if time.time() - b.birth_time < b.lifespan]
        
        new_asteroids = []
        surviving_asteroids = []
        hit_asteroids = set()

        for bullet in active_bullets:
            for i, asteroid in enumerate(asteroids):
                if i in hit_asteroids: continue
                if (bullet.pos - asteroid.pos).length() < asteroid.radius:
                    hit_asteroids.add(i)
                    bullet.lifespan = 0 
                    if asteroid.size > 1:
                        for _ in range(2):
                            new_asteroids.append(Asteroid(asteroid.pos, asteroid.size - 1))
        
        for i, asteroid in enumerate(asteroids):
            if i not in hit_asteroids:
                surviving_asteroids.append(asteroid)

        asteroids = surviving_asteroids + new_asteroids

        for player in players:
            for asteroid in asteroids:
                if (asteroid.pos - player.pos).length() < (asteroid.radius + player.radius):
                    if player.hit():
                        asteroid.vel = pygame.Vector2(0,0) # Effectively remove asteroid
                        if asteroid.size > 1:
                            for _ in range(2):
                                asteroids.append(Asteroid(asteroid.pos, asteroid.size - 1))
                        break 
            
            for bullet in active_bullets:
                if bullet.owner_id != player.player_id and (bullet.pos - player.pos).length() < player.radius:
                    if player.hit():
                        bullet.lifespan = 0

        bullets = [b for b in active_bullets if time.time() - b.birth_time < b.lifespan]
        asteroids = [a for a in asteroids if a.vel.length() > 0]

        if not asteroids:
            num_asteroids = max(3, int(8 * SCALE_FACTOR))
            for _ in range(num_asteroids):
                asteroids.append(spawn_asteroid(3, players))

        screen.fill(BLACK)
        for obj in players + bullets + asteroids:
            obj.draw(screen)
        
        draw_lives(screen, player1, 'left')
        draw_lives(screen, player2, 'right')

        if player1.lives <= 0 or player2.lives <= 0:
            winner = "Player 1" if player2.lives <= 0 else "Player 2"
            text = font.render(f"{winner} Wins!", True, WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
            screen.blit(text, text_rect)
            pygame.display.flip()
            pygame.time.wait(5000)
            running = False

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == '__main__':
    main()
