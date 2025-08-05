import pygame
import random
import math
import sys
import os

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
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

# Game states
MENU = "menu"
CHOOSE_SIDE = "choose_side"
PLAYING = "playing"
PAUSED = "paused"
GAME_OVER = "game_over"

class PenaltyShootout:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Penalty Shootout")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.large_font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 24)
        
        # Game state
        self.state = MENU
        self.difficulty = "normal"
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
        self.ball_pos = [400, 500]
        self.ball_target = [400, 200]
        self.ball_moving = False
        self.animation_timer = 0
        self.goal_animation = False
        self.save_animation = False
        self.animation_delay = 0
        
        # Goal dimensions
        self.goal_left = 300
        self.goal_right = 500
        self.goal_top = 150
        self.goal_bottom = 250
        
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
            "left": pygame.Rect(200, 450, 100, 50),
            "center": pygame.Rect(350, 450, 100, 50),
            "right": pygame.Rect(500, 450, 100, 50),
            "easy": pygame.Rect(200, 300, 100, 50),
            "normal": pygame.Rect(350, 300, 100, 50),
            "hard": pygame.Rect(500, 300, 100, 50),
            "player": pygame.Rect(200, 350, 150, 60),
            "computer": pygame.Rect(450, 350, 150, 60)
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
        gk_x = 400
        gk_y = 200
        
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
            
            # Calculate ball position based on time
            progress = self.animation_timer / 60  # 1 second animation
            
            if progress <= 1:
                # Parabolic trajectory
                x = self.ball_pos[0] + (self.ball_target[0] - self.ball_pos[0]) * progress
                y = self.ball_pos[1] - 100 * math.sin(progress * math.pi) + (self.ball_target[1] - self.ball_pos[1]) * progress
                
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
                        # compare shot vs CPU dive
                        if self.user_shot == self.cpu_keeper_guess:
                            self.save_animation = True
                            was_goal = False  # saved
                        else:
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
            return [self.goal_left + 30, self.goal_top + 50]
        elif direction == "center":
            return [400, self.goal_top + 50]
        else:  # right
            return [self.goal_right - 30, self.goal_top + 50]
    
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
            print(f"Drawing forfeit message: {self.forfeit_message}")  # Debug output
            # Keep the message for a few frames instead of deleting immediately
            # We'll remove it in the reset_game method
        
        # Title
        title = self.large_font.render("Penalty Shootout", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 100))
        self.screen.blit(title, title_rect)
        
        # Difficulty selection
        subtitle = self.font.render("Select Difficulty:", True, WHITE)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH//2, 200))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Difficulty buttons
        for difficulty, rect in [("easy", self.buttons["easy"]), 
                               ("normal", self.buttons["normal"]), 
                               ("hard", self.buttons["hard"])]:
            base_color = YELLOW if difficulty == self.difficulty else GRAY
            hover_color = LIGHT_GRAY
            self.draw_button(rect, difficulty.title(), base_color, hover_color)
            
            # Show difficulty settings
            if difficulty == self.difficulty:
                settings = self.difficulty_settings[difficulty]
                settings_text = self.small_font.render(f"CPU: {settings['cpu_guess_accuracy']*100:.0f}% | You: {settings['player_guess_accuracy']*100:.0f}%", True, WHITE)
                settings_rect = settings_text.get_rect(center=(SCREEN_WIDTH//2, 280))
                self.screen.blit(settings_text, settings_rect)
        
        # Continue button
        continue_rect = pygame.Rect(300, 400, 200, 60)
        self.draw_button(continue_rect, "Continue", RED, (200, 0, 0))
    
    def draw_choose_side(self):
        """Draw the side selection screen"""
        self.screen.fill(GREEN)
        
        # Title
        title = self.large_font.render("Choose Your Side", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 150))
        self.screen.blit(title, title_rect)
        
        # Player button
        player_rect = self.buttons["player"]
        base_color = YELLOW if self.user_is_player else GRAY
        hover_color = LIGHT_GRAY
        self.draw_button(player_rect, "Player", base_color, hover_color)
        
        # Computer button
        computer_rect = self.buttons["computer"]
        base_color = YELLOW if not self.user_is_player else GRAY
        hover_color = LIGHT_GRAY
        self.draw_button(computer_rect, "Computer", base_color, hover_color)
        
        # Start button
        start_rect = pygame.Rect(300, 450, 200, 60)
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
        
        # Draw save direction buttons (when player is saving)
        elif self.current_phase == "player_save" and not self.ball_moving:
            for direction, rect in [("left", self.buttons["left"]), 
                                   ("center", self.buttons["center"]), 
                                   ("right", self.buttons["right"])]:
                base_color = YELLOW if direction == self.player_keeper_guess else GRAY
                hover_color = LIGHT_GRAY
                self.draw_button(rect, direction.title(), base_color, hover_color)
        
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
        
        # Final score
        score_text = self.large_font.render(f"Final Score: You {self.user_score} - Computer {self.computer_score}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH//2, 200))
        self.screen.blit(score_text, score_rect)
        
        # Winner
        if self.user_score > self.computer_score:
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
        
        # Play again button
        play_again_rect = pygame.Rect(300, 380, 200, 60)
        self.draw_button(play_again_rect, "Play Again", BLUE, (0, 0, 200))
        
        # Menu button
        menu_rect = pygame.Rect(300, 460, 200, 60)
        self.draw_button(menu_rect, "Main Menu", GRAY, LIGHT_GRAY)
    
    def reset_game(self):
        """Reset the game state"""
        self.user_score = 0
        self.computer_score = 0
        self.current_phase = "player_shoot"
        self.ball_pos = [400, 500]
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
        self.ball_pos = [400, 500]
        
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
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                if self.state == MENU:
                    # Check difficulty buttons
                    for difficulty, rect in [("easy", self.buttons["easy"]), 
                                           ("normal", self.buttons["normal"]), 
                                           ("hard", self.buttons["hard"])]:
                        if rect.collidepoint(mouse_pos):
                            self.difficulty = difficulty
                    
                    # Check continue button
                    continue_rect = pygame.Rect(300, 400, 200, 60)
                    if continue_rect.collidepoint(mouse_pos):
                        self.state = CHOOSE_SIDE
                
                elif self.state == CHOOSE_SIDE:
                    # Check player button
                    if self.buttons["player"].collidepoint(mouse_pos):
                        self.user_is_player = True
                    
                    # Check computer button
                    if self.buttons["computer"].collidepoint(mouse_pos):
                        self.user_is_player = False
                    
                    # Check start button
                    start_rect = pygame.Rect(300, 450, 200, 60)
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
                                self.user_shot = direction
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
                                self.ball_target = self.get_shot_target(direction)
                                self.ball_moving = True
                                # keep current_phase = "player_shoot" so animate_ball() can resolve
                    
                    # Handle player saving
                    elif self.current_phase == "player_save" and not self.ball_moving:
                        # Check save direction buttons
                        for direction, rect in [("left", self.buttons["left"]), 
                                               ("center", self.buttons["center"]), 
                                               ("right", self.buttons["right"])]:
                            if rect.collidepoint(mouse_pos):
                                self.player_keeper_guess = direction
                                
                                # Your chosen dive direction is `self.player_keeper_guess`
                                # Now decide where CPU actually aims:
                                settings = self.difficulty_settings[self.difficulty]
                                
                                if random.random() < settings["player_guess_accuracy"]:
                                    # CPU shoots where you dive → you save
                                    self.computer_shot = self.player_keeper_guess
                                else:
                                    # CPU shoots elsewhere → you likely miss
                                    wrong = [d for d in self.shot_directions if d != self.player_keeper_guess]
                                    self.computer_shot = random.choice(wrong)
                                
                                # start animation:
                                self.ball_target = self.get_shot_target(self.computer_shot)
                                self.ball_moving = True
                                self.current_phase = "cpu_shoot"
                
                elif self.state == PAUSED:
                    # Resume?
                    if self.resume_btn.collidepoint(mouse_pos):
                        self.state = PLAYING
                    # Quit (forfeit)
                    elif self.quit_btn.collidepoint(mouse_pos):
                        # optional: flash a forfeit message
                        self.forfeit_message = "You forfeited the match!"
                        print("Forfeit message set!")  # Debug output
                        # reset and go back to main menu
                        self.reset_game()
                        self.state = MENU
                    return True  # swallow other clicks while paused
                
                elif self.state == GAME_OVER:
                    # Check play again button
                    play_again_rect = pygame.Rect(300, 380, 200, 60)
                    if play_again_rect.collidepoint(mouse_pos):
                        self.state = PLAYING
                        self.reset_game()
                    
                    # Check menu button
                    menu_rect = pygame.Rect(300, 460, 200, 60)
                    if menu_rect.collidepoint(mouse_pos):
                        self.state = MENU
        
        return True
    
    def update_game(self):
        """Update game logic"""
        if self.state != PLAYING:
            return
        
        # Animate ball
        self.animate_ball()
        
        # Handle CPU shooting phase setup (automatic)
        if self.current_phase == "cpu_shoot" and not self.ball_moving and not self.goal_animation and not self.save_animation:
            # Switch to player save phase so player can choose dive
            self.current_phase = "player_save"
        
        # Handle round completion
        if self.goal_animation or self.save_animation:
            self.animation_delay += 1
            if self.animation_delay > 120:  # Wait 2 seconds (60 FPS * 2)
                # Clear animations & reset ball
                self.goal_animation = False
                self.save_animation = False
                self.animation_delay = 0
                self.ball_pos = [400, 500]
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
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = PenaltyShootout()
    game.run() 