"""
Game Cabinet Menu System - Main launcher for the arcade cabinet.
Players use their joysticks left/right to navigate between available games.
Either player can press their button to launch the selected game. The menu
displays game cards with names and descriptions, scaling up the selected game.
When a game is launched, the menu exits and runs that game's Python file.

Implementation uses pygame for rendering with fullscreen display. Serial input
from ESP32 provides joystick X positions for both players and button states.
Navigation works when either player moves their joystick beyond deadzone
thresholds. Text is scaled to fit within card boundaries to prevent overflow.
"""

import pygame
import serial
import subprocess
import sys
import os

pygame.init()

# Colors
BACKGROUND = (15, 15, 25)
MENU_BG = (30, 30, 45)
SELECTED_BG = (60, 100, 140)
TEXT_COLOR = (220, 220, 230)
HIGHLIGHT_COLOR = (100, 200, 255)
ACCENT_COLOR = (80, 160, 200)

# Screen setup
info = pygame.display.Info()
SCREEN_WIDTH, SCREEN_HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Game Cabinet")

# Serial setup
try:
    ser = serial.Serial("/dev/ttyUSB0", 115200, timeout=0.01)
except serial.SerialException:
    ser = None
    print("Serial port not found. Running with keyboard controls.")

# Font setup - scaled for smaller screens
title_font = pygame.font.Font(None, int(40))
game_font = pygame.font.Font(None, int(32))
subtitle_font = pygame.font.Font(None, int(24))

# Game definitions
GAMES = [
    {
        "name": "Asteroids",
        "description": "Classic space shooter",
        "file": "asteroids.py",
        "color": (255, 100, 100)
    },
    {
        "name": "Symbiosis Garden",
        "description": "Cooperative plant growing",
        "file": "plant.py",
        "color": (100, 255, 150)
    }
]

class GameCard:
    def __init__(self, game_data, index, total_games):
        self.name = game_data["name"]
        self.description = game_data["description"]
        self.file = game_data["file"]
        self.color = game_data["color"]
        self.index = index
        
        # Calculate position and size - scaled for smaller screens
        card_width = min(200, SCREEN_WIDTH // 3)
        card_height = min(180, SCREEN_HEIGHT // 3)
        spacing = 40
        total_width = (card_width * total_games) + (spacing * (total_games - 1))
        start_x = (SCREEN_WIDTH - total_width) // 2
        
        self.x = start_x + (card_width + spacing) * index
        self.y = (SCREEN_HEIGHT - card_height) // 2
        self.width = card_width
        self.height = card_height
        self.target_scale = 1.0
        self.current_scale = 1.0
        
    def update(self, dt, is_selected):
        # Animate scale
        self.target_scale = 1.2 if is_selected else 1.0
        scale_diff = self.target_scale - self.current_scale
        self.current_scale += scale_diff * 5 * dt
        
    def draw(self, surface, is_selected):
        # Calculate scaled dimensions
        scaled_width = int(self.width * self.current_scale)
        scaled_height = int(self.height * self.current_scale)
        scaled_x = self.x + (self.width - scaled_width) // 2
        scaled_y = self.y + (self.height - scaled_height) // 2
        
        # Draw card background
        bg_color = SELECTED_BG if is_selected else MENU_BG
        card_rect = pygame.Rect(scaled_x, scaled_y, scaled_width, scaled_height)
        pygame.draw.rect(surface, bg_color, card_rect, border_radius=15)
        
        # Draw colored accent bar at top
        accent_rect = pygame.Rect(scaled_x, scaled_y, scaled_width, 6)
        pygame.draw.rect(surface, self.color, accent_rect, border_top_left_radius=15, border_top_right_radius=15)
        
        # Draw game name with text fitting
        max_name_width = scaled_width - 20
        name_font_size = 32
        name_font_render = game_font
        name_surf = name_font_render.render(self.name, True, HIGHLIGHT_COLOR if is_selected else TEXT_COLOR)
        
        while name_surf.get_width() > max_name_width and name_font_size > 16:
            name_font_size -= 2
            name_font_render = pygame.font.Font(None, name_font_size)
            name_surf = name_font_render.render(self.name, True, HIGHLIGHT_COLOR if is_selected else TEXT_COLOR)
        
        name_rect = name_surf.get_rect(center=(self.x + self.width // 2, scaled_y + 50))
        surface.blit(name_surf, name_rect)
        
        # Draw description with text fitting
        max_desc_width = scaled_width - 20
        desc_font_size = 24
        desc_font_render = subtitle_font
        desc_surf = desc_font_render.render(self.description, True, TEXT_COLOR)
        
        while desc_surf.get_width() > max_desc_width and desc_font_size > 14:
            desc_font_size -= 2
            desc_font_render = pygame.font.Font(None, desc_font_size)
            desc_surf = desc_font_render.render(self.description, True, TEXT_COLOR)
        
        desc_rect = desc_surf.get_rect(center=(self.x + self.width // 2, scaled_y + 90))
        surface.blit(desc_surf, desc_rect)
        
        # Draw "Press to Play" if selected
        if is_selected:
            play_surf = subtitle_font.render("Press!", True, HIGHLIGHT_COLOR)
            play_rect = play_surf.get_rect(center=(self.x + self.width // 2, scaled_y + scaled_height - 30))
            surface.blit(play_surf, play_rect)
        
        # Draw border
        border_color = HIGHLIGHT_COLOR if is_selected else ACCENT_COLOR
        border_width = 3 if is_selected else 2
        pygame.draw.rect(surface, border_color, card_rect, width=border_width, border_radius=15)

def launch_game(game_file):
    """Launch the selected game"""
    pygame.quit()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    game_path = os.path.join(script_dir, game_file)
    
    # Launch the game using python3
    subprocess.run([sys.executable, game_path])
    
    # When game exits, restart menu
    pygame.init()
    global screen
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)

def main():
    clock = pygame.time.Clock()
    running = True
    
    # Create game cards
    game_cards = [GameCard(game, i, len(GAMES)) for i, game in enumerate(GAMES)]
    selected_index = 0
    
    # Input tracking
    last_joy_x = 2048
    button_pressed = False
    joystick_moved = False
    
    while running:
        dt = clock.tick(60) / 1000.0
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # Read serial input
        p1_joy_x, p2_joy_x = 2048, 2048  # Default neutral
        p1_button, p2_button = 1, 1       # Default unpressed
        
        if ser:
            while ser.in_waiting:
                try:
                    line = ser.readline().decode('utf-8').rstrip()
                    if line:
                        values = line.split("/")
                        if len(values) >= 8:
                            p2_joy_x = int(values[1])
                            p1_joy_x = int(values[3])
                            p1_button = int(values[4])
                            p2_button = int(values[5])
                except (ValueError, IndexError):
                    pass
        else:
            # Keyboard fallback
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                p1_joy_x = 500
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                p1_joy_x = 3500
            if keys[pygame.K_SPACE] or keys[pygame.K_RETURN]:
                p1_button = 0
        
        # Handle joystick navigation - either player can navigate
        combined_joy = (p1_joy_x + p2_joy_x) / 2
        
        if (p1_joy_x < 1500 or p2_joy_x < 1500) and not joystick_moved:
            selected_index = (selected_index - 1) % len(GAMES)
            joystick_moved = True
        elif (p1_joy_x > 2500 or p2_joy_x > 2500) and not joystick_moved:
            selected_index = (selected_index + 1) % len(GAMES)
            joystick_moved = True
        elif p1_joy_x >= 1500 and p1_joy_x <= 2500 and p2_joy_x >= 1500 and p2_joy_x <= 2500:
            joystick_moved = False
        
        # Handle button press - either player can launch
        if (p1_button == 0 or p2_button == 0) and not button_pressed:
            selected_game = GAMES[selected_index]
            launch_game(selected_game["file"])
            button_pressed = True
        elif p1_button == 1 and p2_button == 1:
            button_pressed = False
        
        # Update game cards
        for i, card in enumerate(game_cards):
            card.update(dt, i == selected_index)
        
        # Draw
        screen.fill(BACKGROUND)
        
        # Draw title
        title_surf = title_font.render("GAME CABINET", True, HIGHLIGHT_COLOR)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 30))
        screen.blit(title_surf, title_rect)
        
        # Draw subtitle (simplified for small screens)
        subtitle_surf = subtitle_font.render("← Joystick → | Button: Play", True, TEXT_COLOR)
        subtitle_rect = subtitle_surf.get_rect(center=(SCREEN_WIDTH // 2, 60))
        screen.blit(subtitle_surf, subtitle_rect)
        
        # Draw game cards
        for i, card in enumerate(game_cards):
            card.draw(screen, i == selected_index)
        
        # Draw navigation arrows
        if len(GAMES) > 1:
            # Left arrow
            if selected_index > 0:
                arrow_surf = subtitle_font.render("◀", True, ACCENT_COLOR)
                arrow_rect = arrow_surf.get_rect(center=(20, SCREEN_HEIGHT // 2))
                screen.blit(arrow_surf, arrow_rect)
            
            # Right arrow
            if selected_index < len(GAMES) - 1:
                arrow_surf = subtitle_font.render("▶", True, ACCENT_COLOR)
                arrow_rect = arrow_surf.get_rect(center=(SCREEN_WIDTH - 20, SCREEN_HEIGHT // 2))
                screen.blit(arrow_surf, arrow_rect)
        
        # Draw footer
        footer_surf = subtitle_font.render("ESC to exit", True, (100, 100, 120))
        footer_rect = footer_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 20))
        screen.blit(footer_surf, footer_rect)
        
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()
