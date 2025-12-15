import pygame
import sys
import math
import random
from os.path import join, exists
import pytmx # For loading Tiled map files
from settings import *
from groups import CameraGroup
from sprites import Player, Enemy, Sprite, import_folder

class Game:
    def __init__(self): # Initializing the Game class
        pygame.init() # Initializing all imported pygame modules
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE) # Creating the main display surface with specified width and height
        pygame.display.set_caption('FOREST OF THE CRYSTAL KNIGHT') # Setting the window title
        self.clock = pygame.time.Clock() # Creating a clock object to manage the game's frame rate
        self.font = pygame.font.SysFont("arial", 40, bold=True) # Creating a font object for rendering text
        self.ui_font = pygame.font.SysFont("arial", 20, bold=True) # Font for UI elements
        self.title_font = pygame.font.SysFont("arial", 80, bold=True) # Font for titles
        self.state = 'MENU' # Initial game state set to 'MENU'
        self.muted = False # Audio is not muted by default
        self.target_fps = 60  # Target frames per second
        
        self.play_btn = pygame.Rect(0,0,200,60) # Play button rectangle
        self.instruct_btn = pygame.Rect(0,0,200,60) # Instructions button rectangle
        self.back_btn = pygame.Rect(0,0,200,60) # Back button rectangle
        self.resume_btn = pygame.Rect(0,0,200,60) # Resume button rectangle
        self.mute_btn = pygame.Rect(0,0,200,60) # Mute button rectangle
        self.menu_btn = pygame.Rect(0,0,200,60) # Menu button rectangle
        self.end_play_btn = pygame.Rect(0,0,200,60) # End play button rectangle
        self.end_menu_btn = pygame.Rect(0,0,200,60) # End menu button rectangle
        self.ui_pause_btn = pygame.Rect(0,0,40,40) # Pause button rectangle
        self.ui_mute_btn = pygame.Rect(0,0,40,40) # Mute button rectangle
        
        self.all_sprites = CameraGroup() # Group to hold all sprites with camera functionality
        self.mobs_killed = 0 # Counter for mobs killed
        self.current_music_track = None # Currently playing music track
        self.load_assets() # Loading game assets

    def load_assets(self):
        self.audio = {'shoot': None, 'impact': None} # Dictionary to hold audio assets
        self.music_files = {} # Dictionary to hold music file paths
    
        shoot_path = join(AUDIO_PATH, 'shoot.wav') # Shooting sound effect path
        impact_path = join(AUDIO_PATH, 'impact.ogg') # Impact sound effect path
        
        if exists(shoot_path): 
            self.audio['shoot'] = pygame.mixer.Sound(shoot_path) # Loading shooting sound effect
            self.audio['shoot'].set_volume(0.4) # Setting volume for shooting sound effect
        if exists(impact_path):
            self.audio['impact'] = pygame.mixer.Sound(impact_path) # Loading impact sound effect
            self.audio['impact'].set_volume(0.4) # Setting volume for impact sound effect
            
        music_path_ogg = join(AUDIO_PATH, 'music.ogg') # Main game music path
        if exists(music_path_ogg): 
            self.music_files['game'] = music_path_ogg # Using OGG if available
        else: 
            self.music_files['game'] = join(AUDIO_PATH, 'music.wav') # Fallback to WAV format
        
        menu_path_ogg = join(AUDIO_PATH, 'menu.ogg') # Menu music path
        if exists(menu_path_ogg): 
            self.music_files['menu'] = menu_path_ogg # Using OGG if available
        else: 
            self.music_files['menu'] = join(AUDIO_PATH, 'menu.wav') # Fallback to WAV format

        boss_path = join(ENEMY_PATH, 'boss') # Path to boss enemy assets
        boss_assets = {} # Dictionary to hold boss animation frames
        
        if exists(boss_path):
            boss_assets['move'] = import_folder(join(boss_path, 'move')) # Loading boss move animation frames
            boss_assets['attack'] = import_folder(join(boss_path, 'attack')) # Loading boss attack animation frames
            boss_assets['teleport'] = import_folder(join(boss_path, 'teleport')) # Loading boss teleport animation frames
            boss_assets['summon'] = import_folder(join(boss_path, 'summon')) # Loading boss summon animation frames
            
            # Fallbacks if specific folders are empty
            if not boss_assets['teleport']: boss_assets['teleport'] = boss_assets['move'] # Fallback to move animation
            if not boss_assets['summon']: boss_assets['summon'] = boss_assets['attack'] # Fallback to attack animation
            if not boss_assets['move']: 
                boss_assets['move'] = import_folder(boss_path) # Load all as move animation

        # Loading enemy animation frames
        self.enemy_frames = {
            'bat': import_folder(join(ENEMY_PATH, 'bat')),
            'blob': import_folder(join(ENEMY_PATH, 'blob')),
            'skeleton': import_folder(join(ENEMY_PATH, 'skeleton')),
            'boss': boss_assets
        }

    def switch_music(self, track_name):
        if self.current_music_track == track_name: # If the track is already playing
            return 
        self.current_music_track = track_name # Updating the current music track
        if track_name in self.music_files and exists(self.music_files[track_name]): # If the track exists
            try:
                pygame.mixer.music.load(self.music_files[track_name]) # Loading the music file
                pygame.mixer.music.set_volume(0.2) # Setting music volume
                pygame.mixer.music.play(-1) # Playing the music on loop
                if self.muted: pygame.mixer.music.pause() # Pausing music if muted
            except: 
                print(f"Error playing music: {track_name}") # Error handling for music playback

    def toggle_mute(self):
        self.muted = not self.muted # Toggling mute state
        vol = 0 if self.muted else 0.4 # Setting volume based on mute state
        if self.audio['shoot']: 
            self.audio['shoot'].set_volume(vol) # Adjusting shoot sound volume
        if self.audio['impact']: 
            self.audio['impact'].set_volume(vol) # Adjusting impact sound volume
        if self.muted: pygame.mixer.music.pause() # Pausing music if muted
        else: 
            pygame.mixer.music.unpause() # Unpausing music if unmuted

# Starting a new game by initializing all necessary components
    def start_new_game(self):
        self.all_sprites = CameraGroup() 
        self.bullet_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()
        self.obstacle_sprites = pygame.sprite.Group()
        self.border_sprites = pygame.sprite.Group()
        
        # Making these variables globally accessible
        global all_sprites, bullet_sprites  
        all_sprites = self.all_sprites
        bullet_sprites = self.bullet_sprites
        
        # Loading the map
        if exists(MAP_PATH):
             self.tmx_data = pytmx.util_pygame.load_pygame(MAP_PATH) # Loading the Tiled map file
        else:
             print("ERROR: Map file not found!")
             return

        self.map_width = self.tmx_data.width * TILE_SIZE # Calculating map width in pixels
        self.map_height = self.tmx_data.height * TILE_SIZE # Calculating map height in pixels
        self.all_sprites.set_map_limits(self.map_width, self.map_height) # Setting map limits for camera group

        for x, y, surf in self.tmx_data.get_layer_by_name('Ground').tiles(): # Iterating through all tiles in the 'Ground' layer
            Sprite((x * TILE_SIZE, y * TILE_SIZE), surf, self.all_sprites, LAYERS['ground'], shrink_hitbox=False) # Creating a Sprite for each ground tile
        for obj in self.tmx_data.get_layer_by_name('Objects'): # Iterating through all objects in the 'Objects' layer
            obj_name = obj.name if obj.name else 'obstacle' # Default name if none provided
            Sprite((obj.x, obj.y), obj.image, [self.all_sprites, self.obstacle_sprites], LAYERS['main'], obj_name=obj_name, shrink_hitbox=True) # Creating a Sprite for each object
        
        # Creating boundary trees around the map
        if exists(TREE_PATH): 
            tree_surf = pygame.image.load(TREE_PATH).convert_alpha() # Loading tree image
            DENSITY = 40 # Distance between trees
            for x in range(-TILE_SIZE * 5, self.map_width + TILE_SIZE * 5, DENSITY): # Placing trees along the top and bottom edges
                for y in range(-TILE_SIZE * 5, TILE_SIZE, DENSITY): # Placing trees above the top edge
                    Sprite((x, y), tree_surf, [self.all_sprites, self.border_sprites], LAYERS['main'], obj_name='border', shrink_hitbox=False) # Top edge
                for y in range(self.map_height - TILE_SIZE, self.map_height + TILE_SIZE * 5, DENSITY): 
                    Sprite((x, y), tree_surf, [self.all_sprites, self.border_sprites], LAYERS['main'], obj_name='border', shrink_hitbox=False) # Bottom edge
            for y in range(0, self.map_height, DENSITY):
                for x in range(-TILE_SIZE * 5, TILE_SIZE, DENSITY): 
                    Sprite((x, y), tree_surf, [self.all_sprites, self.border_sprites], LAYERS['main'], obj_name='border', shrink_hitbox=False) # Left edge
                for x in range(self.map_width - TILE_SIZE, self.map_width + TILE_SIZE * 5, DENSITY): # 
                    Sprite((x, y), tree_surf, [self.all_sprites, self.border_sprites], LAYERS['main'], obj_name='border', shrink_hitbox=False) # Right edge

        for obj in self.tmx_data.get_layer_by_name('Entities'):
            if obj.name == 'Player':
                self.player = Player((obj.x, obj.y), [self.all_sprites], self.obstacle_sprites, self.border_sprites, self.audio, self.all_sprites, self.bullet_sprites) # Creating the player instance

        self.score = 0 # Initializing player score
        self.wave = 1 # Starting at wave 1
        self.mobs_killed = 0 # Resetting mobs killed counter
        self.enemies_remaining = 0 # Enemies remaining in the current wave
        self.enemies_to_spawn = 0 # Enemies left to spawn in the current wave
        self.spawn_timer = 0 # Timer for enemy spawning
        self.wave_cooldown = 0 # Cooldown timer between waves
        self.in_wave = False  # Flag to indicate if currently in a wave
        self.state = 'COUNTDOWN' # Setting game state to countdown before wave starts
        self.countdown_start = pygame.time.get_ticks() # Recording the start time of the countdown
        self.start_new_wave() # Starting the first wave

    def start_new_wave(self):
        self.wave_cooldown = pygame.time.get_ticks() # Recording the time when the new wave starts
        self.in_wave = False # Indicating that the wave has not yet started
        if self.wave % 5 == 0: 
            self.enemies_to_spawn = 1 # Boss wave
        else: 
            self.enemies_to_spawn = 3 + (self.wave * 2) # Regular wave enemy count

    def spawn_logic(self):
        if self.enemies_to_spawn > 0:
            current_time = pygame.time.get_ticks() # Getting the current time in milliseconds
            if current_time - self.spawn_timer > 1000: 
                self.spawn_timer = current_time; self.spawn_enemy() # Spawning an enemy every second
                self.enemies_to_spawn -= 1 # Decreasing the count of enemies left to spawn

    def spawn_enemy(self, forced_type=None, pos=None):
        if forced_type: 
            enemy_type = forced_type # Forcing a specific enemy type
        else:
            options = ['bat'] # Starting with 'bat' as a default enemy type
            if self.wave >= 2: 
                options.append('blob') # Adding 'blob' enemy type from wave 2 onwards
            if self.wave >= 3: 
                options.append('skeleton') # Adding 'skeleton' enemy type from wave 3 onwards
            enemy_type = random.choice(options)
            if self.wave % 5 == 0: 
                enemy_type = 'boss' # Forcing boss type on boss 5th waves 
        
        if pos: x, y = pos 
        else:
            edge = random.choice(['top', 'bottom', 'left', 'right']) # Randomly choosing an edge to spawn the enemy
            if edge == 'top': 
                x = random.randint(0, self.map_width) # Spawning above the top edge
                y = -100 #100 pixels above the map
            elif edge == 'bottom': 
                x = random.randint(0, self.map_width) # Spawning below the bottom edge
                y = self.map_height + 100 #100 pixels below the map
            elif edge == 'left': 
                x = -100 #100 pixels left of the map
                y = random.randint(0, self.map_height) # Spawning left of the left edge
            else: 
                x = self.map_width + 100 #100 pixels right of the map
                y = random.randint(0, self.map_height) # Spawning right of the right edge
        Enemy((x, y), self.player, [self.all_sprites, self.enemy_sprites], self.obstacle_sprites, enemy_type, self.enemy_frames[enemy_type], game_ref=self) # Creating the enemy instance

    def draw_enemy_indicator(self):
        for enemy in self.enemy_sprites:
            if getattr(enemy, 'is_dead', False): # Skipping dead enemies
                continue
            player_vec = pygame.math.Vector2(self.player.rect.center) # Getting the player's position vector
            enemy_vec = pygame.math.Vector2(enemy.rect.center) # Getting the enemy's position vector
            diff = enemy_vec - player_vec # Calculating the difference vector from player to enemy
            if diff.length() > 0:
                direction = diff.normalize()
                base_size = 50 if enemy.enemy_name == 'boss' else 30 # Larger arrow for boss
                color = 'purple' if enemy.enemy_name == 'boss' else 'red' # Different color for boss
                scr_w, scr_h = self.display_surface.get_size() # Getting the current screen dimensions
                center_screen = pygame.math.Vector2(scr_w//2, scr_h//2) # Center of the screen
                arrow_center = center_screen + direction * 100 # Positioning the arrow 100 pixels from the center in the direction of the enemy
                tip = arrow_center + direction * (base_size * 0.6) # Calculating the tip of the arrow
                left_wing = arrow_center + direction.rotate(150) * (base_size * 0.5) # Calculating the left wing of the arrow
                right_wing = arrow_center + direction.rotate(-150) * (base_size * 0.5) # Calculating the right wing of the arrow
                pygame.draw.polygon(self.display_surface, color, [tip, left_wing, right_wing]) # Drawing the arrow on the display surface

    def draw_button(self, text, rect, hover_color='white', normal_color='gray'): # Drawing a button with hover effect
        mouse_pos = pygame.mouse.get_pos() # Getting the current mouse position
        color = hover_color if rect.collidepoint(mouse_pos) else normal_color # Changing color on hover
        pygame.draw.rect(self.display_surface, color, rect, border_radius=12) # Drawing the button rectangle
        pygame.draw.rect(self.display_surface, 'white', rect, 2, border_radius=12) # Drawing the button border
        txt_surf = self.ui_font.render(text, True, 'black' if color == hover_color else 'white') # Rendering the button text
        self.display_surface.blit(txt_surf, txt_surf.get_rect(center=rect.center)) # Drawing the text onto the button 

    def draw_ui_overlay(self):
        w, h = self.display_surface.get_size() # Getting the current screen dimensions
        self.ui_pause_btn.topright = (w - 60, 10) # Positioning the pause button
        self.ui_mute_btn.topright = (w - 10, 10) # Positioning the mute button
        self.draw_button("||", self.ui_pause_btn) # Drawing the pause button
        self.draw_button("M" if not self.muted else "U", self.ui_mute_btn) # Drawing the mute/unmute button
        fps = int(self.clock.get_fps()) # Getting the current frames per second
        fps_txt = self.ui_font.render(f"FPS: {fps}", True, 'yellow') # Rendering the FPS text
        self.display_surface.blit(fps_txt, (10, h - 30)) # Drawing the FPS text on the screen

    def draw_menu(self):
        self.display_surface.fill('#223322') # Filling the background with a dark green color
        w, h = self.display_surface.get_size() # Getting the current screen dimensions
        scale = 1 + math.sin(pygame.time.get_ticks() * 0.005) * 0.05 # Calculating a scaling factor for the title animation
        title_surf = self.title_font.render("FOREST OF THE CRYSTAL KNIGHT", True, '#aaffaa') # Rendering the title text
        title_surf = pygame.transform.rotozoom(title_surf, 0, scale) # Applying scaling to the title surface
        self.display_surface.blit(title_surf, title_surf.get_rect(center=(w//2, h//2 - 150))) # Drawing the title on the screen
        
        cx, cy = w // 2, h // 2 # Center coordinates for buttons
        self.play_btn.center = (cx, cy) # Positioning the play button
        self.instruct_btn.center = (cx, cy + 80) # Positioning the instructions button
        self.draw_button("PLAY GAME", self.play_btn, '#44ff44', '#228822') # Drawing the play button
        self.draw_button("CONTROLS", self.instruct_btn, '#44ff44', '#228822') # Drawing the instructions button

    def draw_pause_menu(self):
        w, h = self.display_surface.get_size() # Getting the current screen dimensions
        overlay = pygame.Surface((w, h), pygame.SRCALPHA); overlay.fill(UI_BG_COLOR) # Creating a semi-transparent overlay
        self.display_surface.blit(overlay, (0,0)) # Drawing the overlay on the display surface
        title = self.title_font.render("PAUSED", True, 'white') # Rendering the paused title text
        self.display_surface.blit(title, title.get_rect(center=(w//2, h//2 - 150))) # Drawing the paused title on the screen
        cx, cy = w // 2, h // 2 # Center coordinates for buttons
        self.resume_btn.center = (cx, cy - 20) # Positioning the resume button
        self.mute_btn.center = (cx, cy + 60)  # Positioning the mute button
        self.menu_btn.center = (cx, cy + 140) # Positioning the main menu button
        self.draw_button("RESUME", self.resume_btn) # Drawing the resume button
        self.draw_button("MUTE MUSIC" if not self.muted else "UNMUTE", self.mute_btn) # Drawing the mute/unmute button
        self.draw_button("MAIN MENU", self.menu_btn) # Drawing the main menu button

    def draw_instructions(self):
        self.display_surface.fill('#222222') # Filling the background with a dark gray color
        w, h = self.display_surface.get_size() # Getting the current screen dimensions
        title = self.title_font.render("HOW TO PLAY", True, 'white'); self.display_surface.blit(title, title.get_rect(center=(w//2, 100))) # Drawing the instructions title
        lines = ["MOVE:  WASD / Arrows", "AIM:   Mouse", "SHOOT: Left Click", "PAUSE: ESC", "FPS:   F Key"] # Instructions text
        for i, line in enumerate(lines):
            txt = self.font.render(line, True, 'white'); self.display_surface.blit(txt, txt.get_rect(center=(w//2, 250 + i * 60))) # Drawing each instruction line
        self.back_btn.center = (w//2, h - 100) # Positioning the back button
        self.draw_button("BACK", self.back_btn) # Drawing the back button

    def draw_victory(self):
        self.all_sprites.custom_draw(self.player) # Drawing all sprites with the player as the focus
        w, h = self.display_surface.get_size() # Getting the current screen dimensions
        overlay = pygame.Surface((w, h), pygame.SRCALPHA); overlay.fill(UI_BG_COLOR) # Creating a semi-transparent overlay
        self.display_surface.blit(overlay, (0,0)) # Drawing the overlay on the display surface
        title = self.title_font.render("VICTORY!", True, '#ffff00'); self.display_surface.blit(title, title.get_rect(center=(w//2, h//2 - 180))) # Drawing the victory title
        
        panel = pygame.Rect(0, 0, 400, 200) # Creating a panel rectangle for stats
        panel.center = (w//2, h//2 - 20) # Centering the panel
        pygame.draw.rect(self.display_surface, '#333333', panel, border_radius=15) # Drawing the panel background
        pygame.draw.rect(self.display_surface, 'white', panel, 3, border_radius=15) # Drawing the panel border
        stats = [f"Kills: {self.mobs_killed}", f"Score: {self.score}", "Rating: S"] # Victory stats
        for i, text in enumerate(stats):
            t = self.font.render(text, True, 'white'); self.display_surface.blit(t, t.get_rect(center=(w//2, h//2 - 80 + i*50))) # Drawing each stat line

        cx, cy = w // 2, h // 2 + 150 # Center coordinates for buttons
        self.end_play_btn.center = (cx - 120, cy) # Positioning the play again button
        self.end_menu_btn.center = (cx + 120, cy) # Positioning the main menu button
        self.draw_button("PLAY AGAIN", self.end_play_btn, '#00ff00', '#008800') # Drawing the play again button
        self.draw_button("MENU", self.end_menu_btn, '#ff0000', '#880000') # Drawing the main menu button

    def draw_game_over(self):
        self.all_sprites.custom_draw(self.player) # Drawing all sprites with the player as the focus
        w, h = self.display_surface.get_size() # Getting the current screen dimensions
        overlay = pygame.Surface((w, h), pygame.SRCALPHA) # Creating a semi-transparent overlay
        overlay.fill(UI_BG_COLOR) # Filling the overlay with the UI background color
        self.display_surface.blit(overlay, (0,0)) # Drawing the overlay on the display surface
        title = self.title_font.render("GAME OVER", True, '#ff0000') # Rendering the game over title
        self.display_surface.blit(title, title.get_rect(center=(w//2, h//2 - 180))) # Drawing the game over title
        stats = [f"Wave: {self.wave}", f"Kills: {self.mobs_killed}", f"Score: {self.score}"] # Game over stats
        for i, text in enumerate(stats):
            t = self.font.render(text, True, 'white') # Rendering each stat line
            self.display_surface.blit(t, t.get_rect(center=(w//2, h//2 - 50 + i*50))) # Drawing each stat line
        cx, cy = w // 2, h // 2 + 150 # Center coordinates for buttons
        self.end_play_btn.center = (cx - 120, cy) # Positioning the retry button
        self.end_menu_btn.center = (cx + 120, cy) # Positioning the main menu button
        self.draw_button("RETRY", self.end_play_btn, '#00ff00', '#008800') # Drawing the retry button
        self.draw_button("MENU", self.end_menu_btn, '#ff0000', '#880000') # Drawing the main menu button

    def run(self):
        while True:
            dt = self.clock.tick(self.target_fps) / 1000  # Delta time in seconds
            current_time = pygame.time.get_ticks() # Current time in milliseconds
            for event in pygame.event.get(): 
                if event.type == pygame.QUIT: pygame.quit(); sys.exit() # Exiting the program
                if event.type == pygame.VIDEORESIZE: 
                    self.all_sprites.set_map_limits(self.map_width, self.map_height) # Adjusting map limits on window resize
                if event.type == pygame.KEYDOWN: # Handling keydown events
                    if event.key == pygame.K_ESCAPE: # Toggling pause state
                        if self.state == 'GAME': 
                            self.state = 'PAUSED' # Pausing the game
                        elif self.state == 'PAUSED': 
                            self.state = 'GAME' # Resuming the game
                    if event.key == pygame.K_f: 
                        self.target_fps = 120 if self.target_fps == 60 else 60 # Toggling FPS between 60 and 120
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.state == 'GAME':
                        if self.ui_pause_btn.collidepoint(event.pos): 
                            self.state = 'PAUSED' # Pausing the game
                        if self.ui_mute_btn.collidepoint(event.pos): 
                            self.toggle_mute() # Toggling mute state
                    if self.state == 'MENU':
                        if self.play_btn.collidepoint(event.pos): self.start_new_game() # Starting a new game
                        if self.instruct_btn.collidepoint(event.pos): 
                            self.state = 'INSTRUCTIONS' # Going to instructions screen
                    elif self.state == 'PAUSED':
                        if self.resume_btn.collidepoint(event.pos): self.state = 'GAME' # Resuming the game
                        if self.mute_btn.collidepoint(event.pos): 
                            self.toggle_mute() # Toggling mute state
                        if self.menu_btn.collidepoint(event.pos): self.state = 'MENU' # Going to main menu
                    elif self.state == 'INSTRUCTIONS':
                        if self.back_btn.collidepoint(event.pos): self.state = 'MENU' # Going back to main menu
                    elif self.state in ['GAME_OVER', 'VICTORY']:
                        if self.end_play_btn.collidepoint(event.pos): 
                            self.start_new_game() # Restarting the game
                        if self.end_menu_btn.collidepoint(event.pos): 
                            self.state = 'MENU' # Going to main menu

            if self.state in ['MENU', 'INSTRUCTIONS', 'GAME_OVER', 'VICTORY']: 
                self.switch_music('menu') # Playing menu music
            else: 
                self.switch_music('game') # Playing game music

            if self.state == 'MENU': 
                self.draw_menu() # Drawing the main menu
            elif self.state == 'INSTRUCTIONS': 
                self.draw_instructions() # Drawing the instructions screen
            elif self.state == 'COUNTDOWN':
                self.all_sprites.custom_draw(self.player) # Drawing all sprites with the player as the focus
                time_elapsed = current_time - self.countdown_start # Calculating elapsed time since countdown started
                w, h = self.display_surface.get_size() # Getting the current screen dimensions
                if time_elapsed < 1000: count_text = "3" # Displaying "3" for the first second
                elif time_elapsed < 2000: count_text = "2" # Displaying "2" for the second second
                elif time_elapsed < 3000: count_text = "1" # Displaying "1" for the third second
                else: self.state = 'GAME'; count_text = "GO!" # Starting the game after countdown
                scale = 1 + (time_elapsed % 1000) / 1000 * 0.5 # Scaling effect for countdown text
                text_surf = self.title_font.render(count_text, True, 'yellow') # Rendering the countdown text
                self.display_surface.blit(text_surf, text_surf.get_rect(center=(w//2, h//2))) # Drawing the countdown text
                self.draw_ui_overlay() # Drawing the UI overlay
            elif self.state == 'PAUSED': 
                self.draw_pause_menu() # Drawing the pause menu
            elif self.state == 'GAME':
                self.player.can_attack = self.in_wave # Allowing player to attack only during waves
                self.all_sprites.update(dt) # Updating all sprites with delta time
                if not self.in_wave:
                    if current_time - self.wave_cooldown > 3000: 
                        self.in_wave = True; self.player.heal(20)  # Starting the wave after cooldown and healing the player
                else:
                    self.spawn_logic()
                    if self.enemies_to_spawn == 0 and len(self.enemy_sprites) == 0:
                        if self.wave == 5: 
                            self.state = 'VICTORY' # Ending the game on victory after wave 5
                        else: self.wave += 1; self.start_new_wave() # Starting the next wave

                hits = pygame.sprite.groupcollide(self.enemy_sprites, self.bullet_sprites, False, True) # Checking for bullet-enemy collisions
                for enemy in hits:
                    if getattr(enemy, 'is_dead', False): 
                        continue # Skipping dead enemies
                    enemy.health -= 1 # Reducing enemy health
                    if self.audio['impact']: self.audio['impact'].play() # Playing impact sound effect
                    
                    if enemy.health <= 0: # Enemy death logic
                        self.mobs_killed += 1 # Incrementing mobs killed counter
                        self.score += 500 if enemy.enemy_name == 'boss' else 10 # Updating score based on enemy type
                        enemy.trigger_death() # Triggering enemy death animation
                        
                        # Boss death logic
                        if enemy.enemy_name == 'boss':
                            for mob in self.enemy_sprites: 
                                if mob != enemy: 
                                    mob.kill() # Removing all other enemies
                            self.state = 'VICTORY' # Ending the game on victory

                for enemy in self.enemy_sprites: # Checking for enemy-player collisions
                    if not getattr(enemy, 'is_dead', False): # Skipping dead enemies
                        if self.player.hitbox.colliderect(enemy.hitbox):
                            damage_val = 30 if enemy.enemy_name == 'boss' else 10 # Damage value based on enemy type
                            self.player.damage(damage_val) # Damaging the player

                if not self.player.alive(): self.state = 'GAME_OVER' # Ending the game on player death

                self.all_sprites.custom_draw(self.player) # Drawing all sprites with the player as the focus
                self.draw_enemy_indicator() # Drawing enemy indicators
                self.draw_ui_overlay() # Drawing the UI overlay
                 
                w, h = self.display_surface.get_size() # Getting the current screen dimensions
                # Rendering and displaying the player's score
                score_surf = self.font.render(f'Score: {self.score}', True, 'white')
                self.display_surface.blit(score_surf, (20, 20))
                
                # Drawing the player's health bar background (black rectangle)
                pygame.draw.rect(self.display_surface, 'black', (20, 60, 200, 20))
                # Calculating the health ratio (current health / max health)
                health_ratio = self.player.health / 100
                # Drawing the player's health bar fill (red rectangle, width based on health ratio)
                pygame.draw.rect(self.display_surface, 'red', (20, 60, 200 * health_ratio, 20))
                # Drawing the health bar border (white outline)
                pygame.draw.rect(self.display_surface, 'white', (20, 60, 200, 20), 2)
                # Rendering and displaying the "HP" label next to the health bar
                hp_txt = self.ui_font.render("HP", True, 'white'); self.display_surface.blit(hp_txt, (20 + 200 + 10, 60))

                # Displaying wave information when not currently in a wave
                if not self.in_wave:
                    # For boss waves (every 5th wave), display "BOSS WAVE" in purple
                    if self.wave % 5 == 0: wave_text = self.title_font.render(f'BOSS WAVE', True, 'purple')
                    # For regular waves, display "WAVE X STARTING..." in yellow
                    else: wave_text = self.font.render(f'WAVE {self.wave} STARTING...', True, 'yellow')
                    # Drawing the wave text centered on screen
                    self.display_surface.blit(wave_text, wave_text.get_rect(center = (w//2, h//2 - 100)))
                else:
                    # During a wave, display the current wave number (e.g., "Wave: 1/5")
                    wave_surf = self.font.render(f'Wave: {self.wave}/5', True, 'white'); self.display_surface.blit(wave_surf, (w - 200, 60))
                    # Calculating total remaining enemies (already spawned + still to spawn)
                    remaining = len(self.enemy_sprites) + self.enemies_to_spawn
                    # Displaying the remaining enemy count in red
                    enemy_surf = self.font.render(f'Enemies: {remaining}', True, 'red'); self.display_surface.blit(enemy_surf, (w - 200, 100))
                
                # Finding if a boss is currently alive on the map
                boss_alive = [e for e in self.enemy_sprites if e.enemy_name == 'boss' and not e.is_dead]
                # If a boss exists, display its health bar
                if boss_alive:
                    boss = boss_alive[0]
                    # Calculating the boss's health ratio for the health bar
                    ratio = boss.health / boss.max_health
                    # Drawing the boss health bar background (black rectangle)
                    pygame.draw.rect(self.display_surface, 'black', (w//2 - 200, 50, 400, 30))
                    # Drawing the boss health bar fill (purple rectangle, width based on health ratio)
                    pygame.draw.rect(self.display_surface, 'purple', (w//2 - 200, 50, 400 * ratio, 30))
                    # Drawing the boss health bar border (white outline)
                    pygame.draw.rect(self.display_surface, 'white', (w//2 - 200, 50, 400, 30), 2)
                    # Rendering and displaying the "CRYSTAL KNIGHT" boss name above the health bar
                    boss_txt = self.font.render("CRYSTAL KNIGHT", True, 'white'); self.display_surface.blit(boss_txt, boss_txt.get_rect(center=(w//2, 30)))

            # Displaying the game over screen when the game state is 'GAME_OVER'
            elif self.state == 'GAME_OVER': self.draw_game_over()
            # Displaying the victory screen when the game state is 'VICTORY'
            elif self.state == 'VICTORY': self.draw_victory()
            pygame.display.update() # Updating the display

if __name__ == '__main__':
    game = Game()
    game.run()