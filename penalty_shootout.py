import pygame
import random
import math
import sys
import os
import json
from datetime import datetime

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (34, 139, 34)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (64, 64, 64)

# Game states
MENU = "menu"
CHOOSE_SIDE = "choose_side"
PLAYING = "playing"
PAUSED = "paused"
GAME_OVER = "game_over"
STATS = "stats"
SETTINGS = "settings"

class PenaltyShootout:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Penalty Shootout")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.large_font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 24)
        
        # Load settings and stats first
        self.settings_file = "game_settings.json"
        self.stats_file = "game_stats.json"
        self.settings = self.load_settings()
        self.stats = self.load_stats()
        
        # Game state
        self.state = MENU
        self.difficulty = self.settings.get("default_difficulty", "normal")
        self.user_score = 0
        self.computer_score = 0
        self.win_score = 5
        self.current_phase = "player_shoot"  # player_shoot, cpu_shoot
        self.user_is_player = True  # True = user is player, False = user is computer
        self.next_phase = None  # Track next phase after animation
        
        # Shootout-specific state
        self.player_kicks = 0      # how many kicks the player has taken
        self.cpu_kicks = 0         # how many kicks the CPU has taken
        self.max_kicks = 5         # initial best-of-five
        self.sudden_death = False  # flag for sudden-death mode
        
        # per-kick results: True=goal, False=miss
        self.player_results = []
        self.cpu_results = []
        self.last_kick_result = None  # Store the result of the last kick
        
        # Animation variables
        self.goal_alpha = 0  # For fade-in animations
        self.save_alpha = 0  # For fade-in animations
        
        # Ball and animation state
        self.ball_pos = [512, 650]
        self.ball_target = [512, 300]
        self.ball_moving = False
        self.animation_timer = 0
        self.goal_animation = False
        self.save_animation = False
        self.animation_delay = 0
        
        # Enhanced Power Meter State
        self.aiming = False          # whether we're in the power-aim phase
        self.aim_timer = 0.0         # elapsed time in the current cycle
        self.aim_duration = 1.0      # time (sec) to fill from 0→1
        self.fill_level = 0.0        # normalized [0.0, 1.0]
        self.selected_power = 0.0    # locked-in power for this shot
        self.aim_direction = None    # remember L/C/R for shot target
        
        # Goal dimensions
        self.goal_left = 400
        self.goal_right = 624
        self.goal_top = 200
        self.goal_bottom = 350
        
        # Shot directions
        self.shot_directions = ["left", "center", "right"]
        self.user_shot = None
        self.computer_shot = None
        self.computer_guess_direction = None
        self.goalkeeper_direction = None
        self.player_keeper_guess = None   # when CPU shoots, you choose
        self.cpu_keeper_guess = None      # when you shoot, CPU "dives"
        
        # Difficulty settings
        self.difficulty_settings = {
            "easy": {
                # CPU almost never saves your shots (10% chance to save)
                "cpu_guess_accuracy": 0.10,
                # You almost always save CPU shots (90% dive correctly)
                "player_guess_accuracy": 0.90,
            },
            "normal": {
                # 40% chance CPU guesses your shot
                "cpu_guess_accuracy": 0.40,
                # 40% chance you guess CPU shot
                "player_guess_accuracy": 0.40,
            },
            "hard": {
                # 60% chance CPU guesses your shot
                "cpu_guess_accuracy": 0.60,
                # 60% chance you guess CPU shot
                "player_guess_accuracy": 0.60,
            }
        }
        
        # Button rectangles
        self.buttons = {
            "left": pygame.Rect(300, 600, 120, 60),
            "center": pygame.Rect(450, 600, 120, 60),
            "right": pygame.Rect(600, 600, 120, 60),
            "easy": pygame.Rect(300, 400, 120, 60),
            "normal": pygame.Rect(450, 400, 120, 60),
            "hard": pygame.Rect(600, 400, 120, 60),
            "player": pygame.Rect(300, 500, 150, 70),
            "computer": pygame.Rect(550, 500, 150, 70)
        }
        
        # Pause button (hamburger) in top-right
        self.pause_btn = pygame.Rect(SCREEN_WIDTH - 50, 10, 40, 30)
        
        # Pause-menu buttons (initialized but hidden until paused)
        self.resume_btn = pygame.Rect(SCREEN_WIDTH//2 - 75, SCREEN_HEIGHT//2 - 20, 150, 40)
        self.quit_btn = pygame.Rect(SCREEN_WIDTH//2 - 75, SCREEN_HEIGHT//2 + 40, 150, 40)
        
        # Load soccer ball sprite from PNG
        self.assets_dir = "assets"
        try:
            # Load the raw sprite
            raw_ball = pygame.image.load(os.path.join(self.assets_dir, 'ball.png')).convert_alpha()
            
            # Create a surface with transparency
            ball_surface = pygame.Surface(raw_ball.get_size(), pygame.SRCALPHA)
            
            # Get the pixel array to process the image
            pixel_array = pygame.PixelArray(raw_ball)
            
            # Create a mask to remove white background
            # Convert white pixels to transparent
            for x in range(raw_ball.get_width()):
                for y in range(raw_ball.get_height()):
                    pixel_color = raw_ball.get_at((x, y))
                    # Check if pixel is close to white (background)
                    if pixel_color[0] > 240 and pixel_color[1] > 240 and pixel_color[2] > 240:
                        # Make white pixels transparent
                        ball_surface.set_at((x, y), (0, 0, 0, 0))
                    else:
                        # Keep non-white pixels as they are
                        ball_surface.set_at((x, y), pixel_color)
            
            # Scale to a smaller size (30x30 pixels)
            self.ball_img = pygame.transform.smoothscale(ball_surface, (30, 30))
            
            # No glow effect - just the ball image
            self.ball_glow = None
            
        except pygame.error as e:
            # Fallback if image loading fails
            print(f"Warning: Could not load ball.png: {e}")
            print("Creating programmatic soccer ball as fallback")
            
            # Create a simple soccer ball programmatically as fallback
            self.ball_img = pygame.Surface((30, 30), pygame.SRCALPHA)
            center = (15, 15)
            radius = 13
            
            # Main ball circle (white)
            pygame.draw.circle(self.ball_img, WHITE, center, radius)
            pygame.draw.circle(self.ball_img, BLACK, center, radius, 2)
            
            # Soccer ball pattern
            points = [
                (center[0] - 6, center[1] - 6),
                (center[0] + 6, center[1] - 6),
                (center[0] + 6, center[1] + 6),
                (center[0] - 6, center[1] + 6),
            ]
            pygame.draw.polygon(self.ball_img, BLACK, points)
            
            # Add some smaller details
            pygame.draw.circle(self.ball_img, BLACK, (center[0] - 4, center[1]), 2)
            pygame.draw.circle(self.ball_img, BLACK, (center[0] + 4, center[1]), 2)
            pygame.draw.circle(self.ball_img, BLACK, (center[0], center[1] - 4), 2)
            pygame.draw.circle(self.ball_img, BLACK, (center[0], center[1] + 4), 2)
            
            # No glow effect - just the ball image
            self.ball_glow = None
    
    def draw_button(self, rect, text, base_color, hover_color):
        """Draw a modern rounded button with hover effects"""
        mouse_over = rect.collidepoint(pygame.mouse.get_pos())
        color = hover_color if mouse_over else base_color
        # draw rounded rect
        pygame.draw.rect(self.screen, color, rect, border_radius=12)
        # border
        pygame.draw.rect(self.screen, BLACK, rect, 2, border_radius=12)
        # text
        lbl = self.font.render(text, True, WHITE)
        self.screen.blit(lbl, lbl.get_rect(center=rect.center))
    
    def draw_text(self, text, font, x, y, fg=WHITE):
        """Draw text with drop shadow"""
        # shadow
        shadow = font.render(text, True, (0,0,0,150))
        self.screen.blit(shadow, shadow.get_rect(center=(x+2,y+2)))
        # actual
        fg_surf = font.render(text, True, fg)
        self.screen.blit(fg_surf, fg_surf.get_rect(center=(x,y)))
    
    def draw_hamburger(self):
        """Draw hamburger menu icon"""
        x, y, w, h = self.pause_btn
        bar_h = 4
        spacing = 6
        color = WHITE
        for i in range(3):
            pygame.draw.rect(self.screen, color,
                             (x, y + i*(bar_h + spacing), w, bar_h), border_radius=2)
    
    def draw_power_meter(self):
        """Draw the power meter bar"""
        if not self.aiming or not self.settings.get("show_power_meter", True):
            return
            
        # Power meter dimensions (positioned under the yellow text, moved right)
        meter_x = 80
        meter_y = 400  # moved down to be under the yellow text
        meter_width = 30
        meter_height = 200
        
        # Draw background track (dark, semi-transparent)
        background_rect = pygame.Rect(meter_x, meter_y - meter_height, meter_width, meter_height)
        pygame.draw.rect(self.screen, DARK_GRAY, background_rect, border_radius=5)
        
        # Calculate fill height
        fill_height = int(meter_height * self.fill_level)
        
        # Choose color based on fill level
        if self.fill_level < 0.33:
            color = (0, 200, 0)  # green
        elif self.fill_level < 0.66:
            color = (200, 200, 0)  # yellow
        else:
            color = (200, 0, 0)  # red
        
        # Draw fill bar (rises from bottom to top)
        if fill_height > 0:
            fill_rect = pygame.Rect(meter_x + 2, meter_y - fill_height, 
                                   meter_width - 4, fill_height)
            pygame.draw.rect(self.screen, color, fill_rect, border_radius=5)
        
        # Draw marker arrow next to current fill level
        marker_y = meter_y - fill_height
        pygame.draw.polygon(self.screen, WHITE, [
            (meter_x + meter_width + 5, marker_y),
            (meter_x + meter_width + 15, marker_y - 5),
            (meter_x + meter_width + 15, marker_y + 5)
        ])
        
        # Draw power percentage
        power_text = self.small_font.render(f"{int(self.fill_level * 100)}%", True, WHITE)
        power_rect = power_text.get_rect(center=(meter_x + meter_width//2, meter_y + 20))
        self.screen.blit(power_text, power_rect)
        
        # Draw instructions
        instruction_text = self.small_font.render("Click to lock power", True, WHITE)
        instruction_rect = instruction_text.get_rect(center=(meter_x + meter_width//2, meter_y + 40))
        self.screen.blit(instruction_text, instruction_rect)
    
    def draw_goal(self):
        """Draw the goal frame"""
        pygame.draw.rect(self.screen, WHITE, (self.goal_left, self.goal_top, 
                                              self.goal_right - self.goal_left, 
                                              self.goal_bottom - self.goal_top), 3)
        
        # Draw goal posts
        pygame.draw.line(self.screen, WHITE, (self.goal_left, self.goal_top), 
                        (self.goal_left, self.goal_bottom), 5)
        pygame.draw.line(self.screen, WHITE, (self.goal_right, self.goal_top), 
                        (self.goal_right, self.goal_bottom), 5)
        pygame.draw.line(self.screen, WHITE, (self.goal_left, self.goal_top), 
                        (self.goal_right, self.goal_top), 5)
    
    def draw_ball(self):
        """Draw the ball at its current position"""
        x, y = int(self.ball_pos[0]), int(self.ball_pos[1])
        
        # Draw ball sprite only (no glow)
        ball_rect = self.ball_img.get_rect(center=(x, y))
        self.screen.blit(self.ball_img, ball_rect)
    
    def draw_goalkeeper(self, direction):
        """Draw the goalkeeper"""
        gk_x = 512
        gk_y = 275
        
        # Draw goalkeeper body
        pygame.draw.circle(self.screen, BLUE, (gk_x, gk_y), 15)
        
        # Draw goalkeeper arms based on direction
        if direction == "left":
            pygame.draw.line(self.screen, BLUE, (gk_x, gk_y), (gk_x - 25, gk_y - 10), 5)
            pygame.draw.line(self.screen, BLUE, (gk_x, gk_y), (gk_x - 25, gk_y + 10), 5)
        elif direction == "right":
            pygame.draw.line(self.screen, BLUE, (gk_x, gk_y), (gk_x + 25, gk_y - 10), 5)
            pygame.draw.line(self.screen, BLUE, (gk_x, gk_y), (gk_x + 25, gk_y + 10), 5)
        else:  # center
            pygame.draw.line(self.screen, BLUE, (gk_x, gk_y), (gk_x, gk_y - 25), 5)
    
    def draw_scoreboard(self):
        """Draw TV-style shootout tracker"""
        radius = 10
        spacing = 30
        x0 = SCREEN_WIDTH//2 - (self.max_kicks*spacing)//2
        y_player = 50
        y_cpu = 80

        # player row
        for i in range(self.max_kicks):
            if i < len(self.player_results):
                color = YELLOW if self.player_results[i] else GRAY
            else:
                color = WHITE
            pygame.draw.circle(self.screen, color, (x0+i*spacing, y_player), radius)

        # cpu row
        for i in range(self.max_kicks):
            if i < len(self.cpu_results):
                color = YELLOW if self.cpu_results[i] else GRAY
            else:
                color = WHITE
            pygame.draw.circle(self.screen, color, (x0+i*spacing, y_cpu), radius)
    
    def draw_turn_indicator(self):
        """Draw whose turn it is"""
        if self.current_phase == "player_shoot":
            text = "YOUR SHOT"
            color = YELLOW
        elif self.current_phase == "player_save":
            text = "SAVE THE SHOT!"
            color = RED
        else:
            text = "CPU SHOT"
            color = RED
        lbl = self.large_font.render(text, True, color)
        rect = lbl.get_rect(center=(SCREEN_WIDTH//2, 120))
        # draw a subtle background box
        pygame.draw.rect(self.screen, BLACK, rect.inflate(20,10))
        self.screen.blit(lbl, rect)
    
    def draw_sudden_death_banner(self):
        """Draw sudden death banner"""
        if self.sudden_death:
            banner = self.large_font.render("⚽ SUDDEN DEATH ⚽", True, RED)
            br = banner.get_rect(center=(SCREEN_WIDTH//2, 30))
            pygame.draw.rect(self.screen, BLACK, br.inflate(30,15))
            self.screen.blit(banner, br)
    
    def animate_ball(self):
        """Animate the ball movement"""
        if self.ball_moving:
            self.animation_timer += 1
            
            # Calculate ball position based on time with power meter
            # 1. Mapping fill level → shot duration
            base_time = 60  # 1 second animation at power=0.5
            speed_factor = 0.5 + self.selected_power  # ranges 0.5 (weak) → 1.5 (strong)
            ball_duration = base_time / speed_factor
            progress = self.animation_timer / ball_duration
            
            if progress <= 1:
                # 2. Mapping fill level → arc height
                x = self.ball_pos[0] + (self.ball_target[0] - self.ball_pos[0]) * progress
                # max_arc = 150, arc_height = max_arc * (1.0 - p)
                arc_height = 150 * (1 - self.selected_power)  # more arc at low power
                y = self.ball_pos[1] - arc_height * math.sin(progress * math.pi) + (self.ball_target[1] - self.ball_pos[1]) * progress
                
                self.ball_pos = [x, y]
                
                # Draw ball during animation (no glow)
                ball_rect = self.ball_img.get_rect(center=(int(x), int(y)))
                self.screen.blit(self.ball_img, ball_rect)
            else:
                self.ball_moving = False
                self.animation_timer = 0
                
                # Check if it's a goal
                in_net = (self.goal_left < self.ball_pos[0] < self.goal_right and 
                          self.goal_top < self.ball_pos[1] < self.goal_bottom)
                
                # Determine if it was a goal
                was_goal = False
                if in_net:
                    if self.current_phase == "player_shoot":
                        # 3. Mapping fill level → keeper's save chance
                        settings = self.difficulty_settings[self.difficulty]
                        base_save = settings["cpu_guess_accuracy"]
                        
                        # reduce save chance by up to 50% at full power
                        modifier = 1.0 - (self.selected_power * 0.5)    
                        # → at p=0   → modifier=1.0  (no change)
                        # → at p=1.0 → modifier=0.5  (halved save chance)
                        final_save_chance = base_save * modifier
                        
                        # When the ball crosses the line you then roll:
                        if random.random() < final_save_chance and self.user_shot == self.cpu_keeper_guess:
                            # CPU "dives" correctly → save
                            self.save_animation = True
                            was_goal = False  # saved
                        else:
                            # goal
                            self.user_score += 1
                            self.goal_animation = True
                            was_goal = True   # goal

                    elif self.current_phase == "cpu_shoot":
                        # compare CPU shot vs your dive
                        if self.computer_shot == self.player_keeper_guess:
                            self.save_animation = True
                            was_goal = False  # saved
                        else:
                            self.computer_score += 1
                            self.goal_animation = True
                            was_goal = True   # goal

                else:
                    # shot went wide
                    self.save_animation = True
                    was_goal = False  # missed
                
                # Store the result for end_of_kick
                self.last_kick_result = was_goal
                
                # Change phase after animation is complete
                if self.next_phase is not None:
                    self.current_phase = self.next_phase
                    self.next_phase = None
    
    def get_shot_target(self, direction):
        """Get the target position for a shot direction"""
        if direction == "left":
            return [self.goal_left + 50, self.goal_top + 75]
        elif direction == "center":
            return [512, self.goal_top + 75]
        else:  # right
            return [self.goal_right - 50, self.goal_top + 75]
    
    def computer_guess(self):
        """Computer makes a guess based on difficulty"""
        settings = self.difficulty_settings[self.difficulty]
        
        # Base accuracy on difficulty
        if random.random() < settings["guess_accuracy"]:
            # Computer guesses correctly
            return self.user_shot
        else:
            # Computer guesses wrong
            wrong_directions = [d for d in self.shot_directions if d != self.user_shot]
            return random.choice(wrong_directions)
    
    def draw_menu(self):
        """Draw the main menu"""
        self.screen.fill(GREEN)
        
        # Show forfeit message if applicable
        if hasattr(self, "forfeit_message"):
            msg = self.small_font.render(self.forfeit_message, True, RED)
            rect = msg.get_rect(center=(SCREEN_WIDTH//2, 150))
            self.screen.blit(msg, rect)
        
        # Title
        title = self.large_font.render("Penalty Shootout", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 100))
        self.screen.blit(title, title_rect)
        
        # Difficulty selection
        subtitle = self.font.render("Select Difficulty:", True, WHITE)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH//2, 200))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Difficulty buttons (centered)
        diff_button_width = 120
        diff_button_height = 50
        diff_button_spacing = 30
        total_diff_width = diff_button_width * 3 + diff_button_spacing * 2
        diff_start_x = (SCREEN_WIDTH - total_diff_width) // 2
        diff_y = 250
        
        for i, difficulty in enumerate(["easy", "normal", "hard"]):
            diff_rect = pygame.Rect(diff_start_x + i * (diff_button_width + diff_button_spacing), diff_y, diff_button_width, diff_button_height)
            base_color = YELLOW if difficulty == self.difficulty else GRAY
            hover_color = LIGHT_GRAY
            self.draw_button(diff_rect, difficulty.title(), base_color, hover_color)
        
        # Show difficulty settings between difficulty buttons and continue button
        settings = self.difficulty_settings[self.difficulty]
        settings_text = self.small_font.render(f"CPU: {settings['cpu_guess_accuracy']*100:.0f}% | You: {settings['player_guess_accuracy']*100:.0f}%", True, WHITE)
        settings_rect = settings_text.get_rect(center=(SCREEN_WIDTH//2, 350))
        self.screen.blit(settings_text, settings_rect)
        
        # Menu buttons (centered and evenly spaced)
        button_width = 200
        button_height = 60
        button_spacing = 20
        total_height = button_height * 3 + button_spacing * 2
        start_y = 400  # Moved up to make room for percentage text
        center_x = SCREEN_WIDTH // 2 - button_width // 2
        
        # Continue button
        continue_rect = pygame.Rect(center_x, start_y, button_width, button_height)
        self.draw_button(continue_rect, "Continue", RED, (200, 0, 0))
        
        # Stats button
        stats_rect = pygame.Rect(center_x, start_y + button_height + button_spacing, button_width, button_height)
        self.draw_button(stats_rect, "Statistics", BLUE, (0, 0, 200))
        
        # Settings button
        settings_rect = pygame.Rect(center_x, start_y + (button_height + button_spacing) * 2, button_width, button_height)
        self.draw_button(settings_rect, "Settings", GRAY, LIGHT_GRAY)
    
    def draw_choose_side(self):
        """Draw the side selection screen"""
        self.screen.fill(GREEN)
        
        # Title
        title = self.large_font.render("Choose Your Side", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 150))
        self.screen.blit(title, title_rect)
        
        # Center the side selection buttons
        button_width = 150
        button_height = 70
        button_spacing = 50
        total_width = button_width * 2 + button_spacing
        start_x = (SCREEN_WIDTH - total_width) // 2
        y_pos = 300
        
        # Player button
        player_rect = pygame.Rect(start_x, y_pos, button_width, button_height)
        base_color = YELLOW if self.user_is_player else GRAY
        hover_color = LIGHT_GRAY
        self.draw_button(player_rect, "Player", base_color, hover_color)
        
        # Computer button
        computer_rect = pygame.Rect(start_x + button_width + button_spacing, y_pos, button_width, button_height)
        base_color = YELLOW if not self.user_is_player else GRAY
        hover_color = LIGHT_GRAY
        self.draw_button(computer_rect, "Computer", base_color, hover_color)
        
        # Start button (centered below the side buttons)
        start_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, y_pos + button_height + 50, 200, 60)
        self.draw_button(start_rect, "Start Game", RED, (200, 0, 0))
    
    def draw_game(self):
        """Draw the game screen"""
        self.screen.fill(GREEN)
        
        # Draw field first
        pygame.draw.rect(self.screen, (0, 100, 0), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
        
        # Draw TV-style scoreboard on top
        self.draw_scoreboard()
        self.draw_turn_indicator()
        self.draw_sudden_death_banner()
        
        # Draw goal
        self.draw_goal()
        
        # Draw ball
        self.draw_ball()
        
        # Draw goalkeeper
        if self.current_phase == "player_shoot" and self.computer_guess_direction:
            self.draw_goalkeeper(self.computer_guess_direction)
        elif self.current_phase == "cpu_shoot" and self.goalkeeper_direction:
            self.draw_goalkeeper(self.goalkeeper_direction)
        
        # Draw shot direction buttons (only when user is shooting)
        if self.current_phase == "player_shoot" and not self.ball_moving:
            for direction, rect in [("left", self.buttons["left"]), 
                                   ("center", self.buttons["center"]), 
                                   ("right", self.buttons["right"])]:
                base_color = YELLOW if direction == self.user_shot else GRAY
                hover_color = LIGHT_GRAY
                self.draw_button(rect, direction.title(), base_color, hover_color)
        
        # Draw power meter instructions when in power-aim phase
        elif self.current_phase == "power_aim":
            # Hide direction buttons during power meter
            instruction_text = self.large_font.render("Click to lock power!", True, YELLOW)
            instruction_rect = instruction_text.get_rect(center=(SCREEN_WIDTH//2, 380))
            self.screen.blit(instruction_text, instruction_rect)
        
        # Draw save direction buttons (when player is saving)
        elif self.current_phase == "player_save" and not self.ball_moving:
            for direction, rect in [("left", self.buttons["left"]), 
                                   ("center", self.buttons["center"]), 
                                   ("right", self.buttons["right"])]:
                base_color = YELLOW if direction == self.player_keeper_guess else GRAY
                hover_color = LIGHT_GRAY
                self.draw_button(rect, direction.title(), base_color, hover_color)
        
        # Draw power meter
        self.draw_power_meter()
        
        # Draw hamburger icon
        self.draw_hamburger()
        
        # If paused: overlay menu
        if self.state == PAUSED:
            # dim the game screen
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0,0,0,180))
            self.screen.blit(overlay, (0,0))

            # Draw Resume & Quit buttons
            self.draw_button(self.resume_btn, "Resume", GRAY, LIGHT_GRAY)
            self.draw_button(self.quit_btn, "Quit", GRAY, LIGHT_GRAY)
        
        # Draw score
        score_text = self.font.render(f"You: {self.user_score}  Computer: {self.computer_score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        
        # Draw turn indicator
        if self.current_phase == "player_shoot":
            turn_text = self.font.render("Your turn to shoot!", True, WHITE)
        elif self.current_phase == "player_save":
            turn_text = self.font.render("Save the shot!", True, WHITE)
        elif self.current_phase == "cpu_shoot":
            turn_text = self.font.render("Computer is shooting...", True, WHITE)
        else:
            turn_text = self.font.render("Waiting...", True, WHITE)
        self.screen.blit(turn_text, (10, 50))
        
        # Draw difficulty and settings
        diff_text = self.small_font.render(f"Difficulty: {self.difficulty.title()}", True, WHITE)
        self.screen.blit(diff_text, (10, 90))
        
        # Show current difficulty settings
        settings = self.difficulty_settings[self.difficulty]
        cpu_acc_text = self.small_font.render(f"CPU Save: {settings['cpu_guess_accuracy']*100:.0f}%", True, WHITE)
        player_acc_text = self.small_font.render(f"Your Save: {settings['player_guess_accuracy']*100:.0f}%", True, WHITE)
        self.screen.blit(cpu_acc_text, (10, 110))
        self.screen.blit(player_acc_text, (10, 130))
        
        # Show power meter effects when aiming
        if self.aiming:
            power_effects = self.small_font.render(f"Power: {int(self.fill_level*100)}% → Speed: {1.0/(0.5 + self.fill_level):.1f}s", True, YELLOW)
            self.screen.blit(power_effects, (10, 150))
            
            # Show save chance modifier
            settings = self.difficulty_settings[self.difficulty]
            base_save = settings["cpu_guess_accuracy"]
            modifier = 1.0 - (self.fill_level * 0.5)
            final_save = base_save * modifier
            save_chance_text = self.small_font.render(f"Save chance: {final_save*100:.0f}% (base: {base_save*100:.0f}%)", True, YELLOW)
            self.screen.blit(save_chance_text, (10, 170))
        
        # Draw result messages with fade-in animations
        if self.goal_animation:
            if self.goal_alpha < 255:
                self.goal_alpha += 5  # fade in speed
            goal_surf = self.large_font.render("GOAL!", True, YELLOW)
            goal_surf.set_alpha(self.goal_alpha)
            rect = goal_surf.get_rect(center=(SCREEN_WIDTH//2, 300))
            self.screen.blit(goal_surf, rect)
        
        if self.save_animation:
            if self.save_alpha < 255:
                self.save_alpha += 5  # fade in speed
            save_surf = self.large_font.render("SAVED!", True, RED)
            save_surf.set_alpha(self.save_alpha)
            rect = save_surf.get_rect(center=(SCREEN_WIDTH//2, 300))
            self.screen.blit(save_surf, rect)
    
    def draw_game_over(self):
        """Draw the game over screen"""
        self.screen.fill(GREEN)
        
        # Show forfeit message if applicable
        if hasattr(self, "forfeit_message"):
            forfeit_text = self.large_font.render(self.forfeit_message, True, RED)
            forfeit_rect = forfeit_text.get_rect(center=(SCREEN_WIDTH//2, 150))
            self.screen.blit(forfeit_text, forfeit_rect)
        
        # Final score
        score_text = self.large_font.render(f"Final Score: You {self.user_score} - Computer {self.computer_score}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH//2, 200))
        self.screen.blit(score_text, score_rect)
        
        # Winner
        if hasattr(self, "forfeit_message"):
            winner_text = self.large_font.render("Computer Wins!", True, RED)
        elif self.user_score > self.computer_score:
            winner_text = self.large_font.render("You Win!", True, YELLOW)
        elif self.computer_score > self.user_score:
            winner_text = self.large_font.render("Computer Wins!", True, RED)
        else:
            winner_text = self.large_font.render("It's a Tie!", True, WHITE)
        
        winner_rect = winner_text.get_rect(center=(SCREEN_WIDTH//2, 250))
        self.screen.blit(winner_text, winner_rect)
        
        # Shootout information
        kicks_text = self.font.render(f"Kicks taken: You {self.player_kicks} - Computer {self.cpu_kicks}", True, WHITE)
        kicks_rect = kicks_text.get_rect(center=(SCREEN_WIDTH//2, 300))
        self.screen.blit(kicks_text, kicks_rect)
        
        if self.sudden_death:
            sudden_death_text = self.font.render("Sudden Death Mode", True, RED)
            sudden_death_rect = sudden_death_text.get_rect(center=(SCREEN_WIDTH//2, 330))
            self.screen.blit(sudden_death_text, sudden_death_rect)
        
        # Play again button (centered)
        play_again_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, 450, 200, 60)
        self.draw_button(play_again_rect, "Play Again", BLUE, (0, 0, 200))
        
        # Menu button (centered)
        menu_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, 530, 200, 60)
        self.draw_button(menu_rect, "Main Menu", GRAY, LIGHT_GRAY)
    
    def reset_game(self):
        """Reset the game state"""
        self.user_score = 0
        self.computer_score = 0
        self.current_phase = "player_shoot"
        self.ball_pos = [512, 650]
        self.ball_moving = False
        self.animation_timer = 0
        self.goal_animation = False
        self.save_animation = False
        self.animation_delay = 0
        self.user_shot = None
        self.computer_shot = None
        self.computer_guess_direction = None
        self.goalkeeper_direction = None
        self.player_keeper_guess = None
        self.cpu_keeper_guess = None
        self.next_phase = None
        self.goal_alpha = 0
        self.save_alpha = 0
        
        # Reset ball position for sprite
        self.ball_pos = [512, 650]
        
        # NEW: Reset shootout-specific state
        self.player_kicks = 0
        self.cpu_kicks = 0
        self.sudden_death = False
        
        # NEW: Clear per-kick results
        self.player_results = []
        self.cpu_results = []
        self.last_kick_result = None
        
        # Clear forfeit message when starting new game
        if hasattr(self, "forfeit_message"):
            del self.forfeit_message
        
        # Reset power meter
        self.aiming = False
        self.aim_timer = 0.0
        self.fill_level = 0.0
        self.selected_power = 0.0
        self.aim_direction = None
        
        # Load statistics
        self.stats_file = "game_stats.json"
        self.stats = self.load_stats()
        
        # Reset stats recording flag
        if hasattr(self, "stats_recorded"):
            del self.stats_recorded
        

    
    def load_stats(self):
        """Load statistics from file"""
        try:
            with open(self.stats_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"games": [], "total_games": 0, "wins": 0, "losses": 0, "ties": 0}
    
    def save_stats(self):
        """Save statistics to file"""
        with open(self.stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2)
    
    def record_game_stats(self):
        """Record current game statistics"""
        game_stats = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "difficulty": self.difficulty,
            "player_score": self.user_score,
            "cpu_score": self.computer_score,
            "player_kicks": self.player_kicks,
            "cpu_kicks": self.cpu_kicks,
            "sudden_death": self.sudden_death,
            "forfeited": hasattr(self, "forfeit_message")
        }
        
        # Calculate accuracy
        if self.player_kicks > 0:
            goals_scored = sum(self.player_results)
            game_stats["player_accuracy"] = goals_scored / self.player_kicks
        else:
            game_stats["player_accuracy"] = 0.0
        
        self.stats["games"].append(game_stats)
        self.stats["total_games"] += 1
        
        # Update win/loss/ties
        if self.user_score > self.computer_score:
            self.stats["wins"] += 1
        elif self.computer_score > self.user_score:
            self.stats["losses"] += 1
        else:
            self.stats["ties"] += 1
        
        self.save_stats()
    
    def load_settings(self):
        """Load settings from file"""
        try:
            with open(self.settings_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "default_difficulty": "normal",
                "sound_volume": 0.7,
                "show_power_meter": True,
                "show_instructions": True,
                "ball_speed": 1.0
            }
    
    def save_settings(self):
        """Save settings to file"""
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=2)
    
    def draw_settings_screen(self):
        """Draw the settings screen"""
        self.screen.fill(GREEN)
        
        # Title
        title = self.large_font.render("Game Settings", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 50))
        self.screen.blit(title, title_rect)
        
        # Settings options
        y_pos = 120
        line_height = 50
        
        # Default difficulty
        diff_text = self.font.render(f"Default Difficulty: {self.settings['default_difficulty'].title()}", True, WHITE)
        diff_rect = diff_text.get_rect(center=(SCREEN_WIDTH//2, y_pos))
        self.screen.blit(diff_text, diff_rect)
        
        # Difficulty buttons
        y_pos += 60
        for difficulty in ["easy", "normal", "hard"]:
            btn_rect = pygame.Rect(200 + (difficulty == "easy") * 100, y_pos, 100, 40)
            color = YELLOW if self.settings["default_difficulty"] == difficulty else GRAY
            self.draw_button(btn_rect, difficulty.title(), color, LIGHT_GRAY)
        
        # Sound volume
        y_pos += 80
        vol_text = self.font.render(f"Sound Volume: {int(self.settings['sound_volume'] * 100)}%", True, WHITE)
        vol_rect = vol_text.get_rect(center=(SCREEN_WIDTH//2, y_pos))
        self.screen.blit(vol_text, vol_rect)
        
        # Volume slider
        y_pos += 40
        vol_slider_rect = pygame.Rect(200, y_pos, 400, 20)
        pygame.draw.rect(self.screen, GRAY, vol_slider_rect)
        vol_fill_rect = pygame.Rect(200, y_pos, int(400 * self.settings['sound_volume']), 20)
        pygame.draw.rect(self.screen, BLUE, vol_fill_rect)
        
        # Toggle options
        y_pos += 60
        toggle_texts = [
            ("Show Power Meter", "show_power_meter"),
            ("Show Instructions", "show_instructions")
        ]
        
        for text, setting_key in toggle_texts:
            toggle_text = self.font.render(text, True, WHITE)
            toggle_rect = toggle_text.get_rect(center=(SCREEN_WIDTH//2 - 100, y_pos))
            self.screen.blit(toggle_text, toggle_rect)
            
            # Toggle button
            toggle_btn_rect = pygame.Rect(SCREEN_WIDTH//2 + 50, y_pos - 15, 60, 30)
            color = GREEN if self.settings[setting_key] else RED
            self.draw_button(toggle_btn_rect, "ON" if self.settings[setting_key] else "OFF", color, LIGHT_GRAY)
            y_pos += 40
        
        # Back button
        back_rect = pygame.Rect(300, 500, 200, 60)
        self.draw_button(back_rect, "Back to Menu", GRAY, LIGHT_GRAY)
    
    def draw_stats_screen(self):
        """Draw the statistics screen"""
        self.screen.fill(GREEN)
        
        # Title
        title = self.large_font.render("Game Statistics", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 50))
        self.screen.blit(title, title_rect)
        
        # Overall stats
        total_games = self.stats["total_games"]
        wins = self.stats["wins"]
        losses = self.stats["losses"]
        ties = self.stats["ties"]
        
        if total_games > 0:
            win_rate = (wins / total_games) * 100
        else:
            win_rate = 0
        
        # Display stats
        y_pos = 120
        line_height = 30
        
        stats_texts = [
            f"Total Games: {total_games}",
            f"Wins: {wins}",
            f"Losses: {losses}",
            f"Ties: {ties}",
            f"Win Rate: {win_rate:.1f}%"
        ]
        
        for text in stats_texts:
            stat_text = self.font.render(text, True, WHITE)
            stat_rect = stat_text.get_rect(center=(SCREEN_WIDTH//2, y_pos))
            self.screen.blit(stat_text, stat_rect)
            y_pos += line_height
        
        # Recent games
        y_pos += 20
        recent_title = self.font.render("Recent Games:", True, WHITE)
        recent_rect = recent_title.get_rect(center=(SCREEN_WIDTH//2, y_pos))
        self.screen.blit(recent_title, recent_rect)
        y_pos += line_height
        
        # Show last 5 games
        recent_games = self.stats["games"][-5:] if self.stats["games"] else []
        for game in recent_games:
            result = "W" if game["player_score"] > game["cpu_score"] else "L" if game["player_score"] < game["cpu_score"] else "T"
            game_text = f"{result} {game['player_score']}-{game['cpu_score']} ({game['difficulty']})"
            game_stat = self.small_font.render(game_text, True, WHITE)
            game_rect = game_stat.get_rect(center=(SCREEN_WIDTH//2, y_pos))
            self.screen.blit(game_stat, game_rect)
            y_pos += 25
        
        # Back button (centered)
        back_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, 650, 200, 60)
        self.draw_button(back_rect, "Back to Menu", GRAY, LIGHT_GRAY)
    
    def end_of_kick(self, was_goal):
        """Handle end-of-kick logic for shootout rules"""
        # was_goal is a boolean you pass in:
        #   True  → shooter scored
        #   False → shooter was saved/missed
        
        # 1) count the kick and record result
        if self.current_phase == "player_shoot":
            self.player_kicks += 1
            self.player_results.append(was_goal)
        elif self.current_phase == "cpu_shoot":
            self.cpu_kicks += 1
            self.cpu_results.append(was_goal)

        # 2) check insurmountable lead
        lead = self.user_score - self.computer_score
        if lead > 0:
            # player leads by `lead`; CPU has (max_kicks - cpu_kicks) kicks left
            if lead > (self.max_kicks - self.cpu_kicks):
                self.state = GAME_OVER
                return
        elif lead < 0:
            # CPU leads; player has (max_kicks - player_kicks) kicks left
            if -lead > (self.max_kicks - self.player_kicks):
                self.state = GAME_OVER
                return

        # 3) after five each, if tied → sudden death
        if self.player_kicks == self.max_kicks and self.cpu_kicks == self.max_kicks:
            if self.user_score != self.computer_score:
                self.state = GAME_OVER
                return
            self.sudden_death = True

        # 4) pick next phase (always alternate)
        if self.current_phase == "player_shoot":
            self.current_phase = "cpu_shoot"
        else:
            self.current_phase = "player_shoot"
    
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                # Handle spacebar for power meter
                if event.key == pygame.K_SPACE and self.current_phase == "power_aim":
                    self.selected_power = self.fill_level
                    self.aiming = False
                    self.current_phase = "player_shoot"
                    self.user_shot = self.aim_direction
                    
                    # CPU picks a dive direction based on difficulty
                    settings = self.difficulty_settings[self.difficulty]
                    
                    if random.random() < settings["cpu_guess_accuracy"]:
                        # CPU dives correctly
                        self.cpu_keeper_guess = self.user_shot
                    else:
                        # CPU dives wrong
                        wrong = [d for d in self.shot_directions if d != self.user_shot]
                        self.cpu_keeper_guess = random.choice(wrong)
                    
                    # now kick off the animation as before:
                    self.ball_target = self.get_shot_target(self.user_shot)
                    self.ball_moving = True
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                if self.state == MENU:
                    # Check difficulty buttons
                    # Calculate button positions (same as in draw_menu)
                    button_width = 200
                    button_height = 60
                    button_spacing = 20
                    start_y = 400  # Moved up to match draw_menu
                    center_x = SCREEN_WIDTH // 2 - button_width // 2
                    
                    # Check difficulty buttons (same positions as in draw_menu)
                    diff_button_width = 120
                    diff_button_height = 50
                    diff_button_spacing = 30
                    total_diff_width = diff_button_width * 3 + diff_button_spacing * 2
                    diff_start_x = (SCREEN_WIDTH - total_diff_width) // 2
                    diff_y = 250
                    
                    for i, difficulty in enumerate(["easy", "normal", "hard"]):
                        diff_rect = pygame.Rect(diff_start_x + i * (diff_button_width + diff_button_spacing), diff_y, diff_button_width, diff_button_height)
                        if diff_rect.collidepoint(mouse_pos):
                            self.difficulty = difficulty
                    
                    # Check continue button
                    continue_rect = pygame.Rect(center_x, start_y, button_width, button_height)
                    if continue_rect.collidepoint(mouse_pos):
                        self.state = CHOOSE_SIDE
                    
                    # Check stats button
                    stats_rect = pygame.Rect(center_x, start_y + button_height + button_spacing, button_width, button_height)
                    if stats_rect.collidepoint(mouse_pos):
                        self.state = STATS
                    
                    # Check settings button
                    settings_rect = pygame.Rect(center_x, start_y + (button_height + button_spacing) * 2, button_width, button_height)
                    if settings_rect.collidepoint(mouse_pos):
                        self.state = SETTINGS
                
                elif self.state == CHOOSE_SIDE:
                    # Calculate button positions (same as in draw_choose_side)
                    button_width = 150
                    button_height = 70
                    button_spacing = 50
                    total_width = button_width * 2 + button_spacing
                    start_x = (SCREEN_WIDTH - total_width) // 2
                    y_pos = 300
                    
                    # Check player button
                    player_rect = pygame.Rect(start_x, y_pos, button_width, button_height)
                    if player_rect.collidepoint(mouse_pos):
                        self.user_is_player = True
                    
                    # Check computer button
                    computer_rect = pygame.Rect(start_x + button_width + button_spacing, y_pos, button_width, button_height)
                    if computer_rect.collidepoint(mouse_pos):
                        self.user_is_player = False
                    
                    # Check start button
                    start_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, y_pos + button_height + 50, 200, 60)
                    if start_rect.collidepoint(mouse_pos):
                        self.state = PLAYING
                        self.reset_game()
                
                elif self.state == PLAYING:
                    # Check pause button first
                    if self.pause_btn.collidepoint(mouse_pos):
                        # go into PAUSED state
                        self.state = PAUSED
                        return True
                    
                    # Handle player shooting
                    if self.current_phase == "player_shoot" and not self.ball_moving:
                        # Check shot direction buttons
                        for direction, rect in [("left", self.buttons["left"]), 
                                               ("center", self.buttons["center"]), 
                                               ("right", self.buttons["right"])]:
                            if rect.collidepoint(mouse_pos):
                                if not self.aiming:
                                    # First click: enter power-aim phase
                                    self.aiming = True
                                    self.aim_timer = 0.0
                                    self.fill_level = 0.0
                                    self.aim_direction = direction
                                    self.current_phase = "power_aim"
                                else:
                                    # Second click: lock power and shoot
                                    self.selected_power = self.fill_level
                                    self.aiming = False
                                    self.current_phase = "player_shoot"
                                    self.user_shot = self.aim_direction
                                    
                                    # CPU picks a dive direction based on difficulty
                                    settings = self.difficulty_settings[self.difficulty]
                                    
                                    if random.random() < settings["cpu_guess_accuracy"]:
                                        # CPU dives correctly
                                        self.cpu_keeper_guess = self.user_shot
                                    else:
                                        # CPU dives wrong
                                        wrong = [d for d in self.shot_directions if d != self.user_shot]
                                        self.cpu_keeper_guess = random.choice(wrong)
                                    
                                    # now kick off the animation as before:
                                    self.ball_target = self.get_shot_target(self.user_shot)
                                    self.ball_moving = True
                    
                    # Handle player saving
                    elif self.current_phase == "player_save" and not self.ball_moving:
                        # Check save direction buttons
                        for direction, rect in [("left", self.buttons["left"]), 
                                               ("center", self.buttons["center"]), 
                                               ("right", self.buttons["right"])]:
                            if rect.collidepoint(mouse_pos):
                                self.player_keeper_guess = direction
                                
                                # CPU has already decided where to shoot (in update_game)
                                # Just start the animation with the pre-determined shot
                                self.ball_target = self.get_shot_target(self.computer_shot)
                                self.ball_moving = True
                                self.current_phase = "cpu_shoot"
                
                elif self.state == PAUSED:
                    # Resume?
                    if self.resume_btn.collidepoint(mouse_pos):
                        self.state = PLAYING
                    # Quit (forfeit)
                    elif self.quit_btn.collidepoint(mouse_pos):
                        # Set forfeit message and go to game over state
                        self.forfeit_message = "You forfeited the match!"
                        print("Forfeit message set!")  # Debug output
                        # Set computer as winner and go to game over
                        self.computer_score = 5
                        self.user_score = 0
                        self.state = GAME_OVER
                    return True  # swallow other clicks while paused
                
                elif self.state == GAME_OVER:
                    # Record stats when game ends
                    if not hasattr(self, "stats_recorded"):
                        self.record_game_stats()
                        self.stats_recorded = True
                    
                    # Check play again button
                    play_again_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, 450, 200, 60)
                    if play_again_rect.collidepoint(mouse_pos):
                        self.state = PLAYING
                        self.reset_game()
                    
                    # Check menu button
                    menu_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, 530, 200, 60)
                    if menu_rect.collidepoint(mouse_pos):
                        self.state = MENU
                
                elif self.state == STATS:
                    # Check back button
                    back_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, 650, 200, 60)
                    if back_rect.collidepoint(mouse_pos):
                        self.state = MENU
                
                elif self.state == SETTINGS:
                    # Check difficulty buttons
                    y_pos = 180
                    for difficulty in ["easy", "normal", "hard"]:
                        btn_rect = pygame.Rect(200 + (difficulty == "easy") * 100, y_pos, 100, 40)
                        if btn_rect.collidepoint(mouse_pos):
                            self.settings["default_difficulty"] = difficulty
                            self.difficulty = difficulty
                            self.save_settings()
                    
                    # Check toggle buttons
                    y_pos = 320
                    for setting_key in ["show_power_meter", "show_instructions"]:
                        toggle_btn_rect = pygame.Rect(SCREEN_WIDTH//2 + 50, y_pos - 15, 60, 30)
                        if toggle_btn_rect.collidepoint(mouse_pos):
                            self.settings[setting_key] = not self.settings[setting_key]
                            self.save_settings()
                        y_pos += 40
                    
                    # Check back button
                    back_rect = pygame.Rect(300, 500, 200, 60)
                    if back_rect.collidepoint(mouse_pos):
                        self.state = MENU
        
        return True
    
    def update_game(self):
        """Update game logic"""
        if self.state != PLAYING:
            return
        
        # Update power meter fill animation
        if self.aiming:
            dt = 1.0 / FPS  # delta time
            self.aim_timer += dt
            # loop every aim_duration
            self.fill_level = (self.aim_timer % self.aim_duration) / self.aim_duration
        
        # Animate ball
        self.animate_ball()
        
        # Handle CPU shooting phase setup (automatic)
        if self.current_phase == "cpu_shoot" and not self.ball_moving and not self.goal_animation and not self.save_animation:
            # Switch to player save phase so player can choose dive
            self.current_phase = "player_save"
        
        # Handle CPU shot decision when entering player_save phase
        if self.current_phase == "player_save" and self.computer_shot is None:
            # CPU decides where to shoot BEFORE player chooses dive direction
            settings = self.difficulty_settings[self.difficulty]
            
            # CPU randomly picks a direction (not influenced by player's choice)
            self.computer_shot = random.choice(self.shot_directions)
        
        # Handle round completion
        if self.goal_animation or self.save_animation:
            self.animation_delay += 1
            if self.animation_delay > 120:  # Wait 2 seconds (60 FPS * 2)
                # Clear animations & reset ball
                self.goal_animation = False
                self.save_animation = False
                self.animation_delay = 0
                self.ball_pos = [512, 650]  # Reset to original position
                self.user_shot = None
                self.computer_shot = None
                self.computer_guess_direction = None
                
                # Call our new helper with the stored result
                if self.last_kick_result is not None:
                    self.end_of_kick(self.last_kick_result)
                    self.last_kick_result = None
    
    def run(self):
        """Main game loop"""
        running = True
        
        while running:
            running = self.handle_events()
            self.update_game()
            
            # Draw based on state
            if self.state == MENU:
                self.draw_menu()
            elif self.state == CHOOSE_SIDE:
                self.draw_choose_side()
            elif self.state == PLAYING:
                self.draw_game()
            elif self.state == PAUSED:
                self.draw_game()  # Draw game with pause overlay
            elif self.state == GAME_OVER:
                self.draw_game_over()
            elif self.state == STATS:
                self.draw_stats_screen()
            elif self.state == SETTINGS:
                self.draw_settings_screen()
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = PenaltyShootout()
    game.run() 