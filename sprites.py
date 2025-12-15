import pygame
import math
import random
import os
from os.path import join, exists
from settings import *

def import_folder(path): # Function to import all images from a folder and return them as a list of surfaces
    surface_list = []
    if not exists(path):
        return []

    all_files = os.listdir(path) # List all files in the given directory
    image_files = [] 
    for filename in all_files: # Filter only .png files
        if filename.endswith('.png'):
            image_files.append(filename) # Adding the .png file to the image_files list
    
    def get_number_from_filename(filename): # Function to extract number from filename for sorting
        name_parts = filename.split('.') # Splitting filename to get only the number
        number_text = name_parts[0] 
        return int(number_text) # Converting the extracted number text to an integer

    image_files.sort(key=get_number_from_filename) # Sorting the image files based on the extracted number

    for image in image_files:
        full_path = join(path, image) # Creating the full path to the image file
        image_surf = pygame.image.load(full_path).convert_alpha() # Loading the image as a surface with alpha [alpha = transparency]
        surface_list.append(image_surf) # Adding the loaded surface to the surface_list
    return surface_list

class Sprite(pygame.sprite.Sprite): 
    def __init__(self, pos, surf, groups, z_layer, obj_name=None, shrink_hitbox=False): 
        super().__init__(groups) # Initializing the parent class (pygame.sprite.Sprite)
        self.image = surf # Setting the sprite's image to the provided surface  
        self.rect = self.image.get_rect(topleft=pos) # Setting the sprite's rectangle based on the image's size and position
        self.z = z_layer # Setting the sprite's layer for rendering order
        self.obj_name = obj_name or "obstacle" # Naming the sprite object, default is "obstacle"
        
        if z_layer == LAYERS['main']: # Only main layer sprites need hitboxes for collision
            if shrink_hitbox: 
                self.hitbox = self.rect.inflate(-self.rect.width * 0.2, -self.rect.height * 0.5) # Shrinking [-] hitbox for better collision [20% width, 50% height]
                self.hitbox.bottom = self.rect.bottom - 5 # Aligning the bottom of the hitbox slightly above the sprite's bottom
            else:
                self.hitbox = self.rect.inflate(0, 0) # Hitbox same as rect
        else:
            self.hitbox = self.rect # For layers other than main, hitbox is same as rect

class Gun(pygame.sprite.Sprite): 
    def __init__(self, player, groups): # Initializing the Gun class
        super().__init__(groups) # Calling the parent class's to initialize the child class
        self.player = player
        self.z = LAYERS['main'] # Setting the gun's layer to main
        
        gun_full_path = join(GUN_PATH, 'gun.png')
        if exists(gun_full_path):
            self.original_image = pygame.image.load(gun_full_path).convert_alpha() # Loading the gun image
            self.original_image = pygame.transform.scale(self.original_image, (60, 30)) # Scaling the gun image to desired size
        else:
            print("WARNING: gun.png missing")
            self.original_image = pygame.Surface((20, 10)) # Creating a placeholder surface
            self.original_image.fill('black') # Filling the placeholder with black color
            
        self.image = self.original_image
        self.rect = self.image.get_rect(center = player.rect.center) # Setting the gun's rectangle centered on the player
        self.offset_dist = 60 # Distance from player center to gun center
        self.player_direction = pygame.math.Vector2(1, 0) # Initial direction vector pointing right

    def update(self, dt):
        mouse_pos = pygame.mouse.get_pos() # Getting the current mouse position
        screen_w, screen_h = pygame.display.get_surface().get_size() # Getting the screen dimensions
        offset_x = self.player.rect.centerx - screen_w // 2 # Calculating the x-offset based on player position
        offset_y = self.player.rect.centery - screen_h // 2 # Calculating the y-offset based on player position
        
        map_w, map_h = 4000, 4000 
        for group in self.player.groups(): 
            if hasattr(group, 'map_width'): # hasattr checks if the group has the attribute 'map_width'
                map_w = group.map_width 
                map_h = group.map_height 
                break # Exiting loop once map dimensions are found
        
        if offset_x < 0: offset_x = 0 # Preventing camera from going beyond left boundary
        if offset_y < 0: offset_y = 0 # Preventing camera from going beyond top boundary
        if offset_x > map_w - screen_w: offset_x = map_w - screen_w # Preventing camera from going beyond right boundary
        if offset_y > map_h - screen_h: offset_y = map_h - screen_h # Preventing camera from going beyond bottom boundary

        player_screen_x = self.player.rect.centerx - offset_x # Calculating player's screen x-coordinate
        player_screen_y = self.player.rect.centery - offset_y # Calculating player's screen y-coordinate
        
        rel_x = mouse_pos[0] - player_screen_x # Relative x from player to mouse
        rel_y = mouse_pos[1] - player_screen_y # Relative y from player to mouse
        self.angle = math.degrees(math.atan2(-rel_y, rel_x)) # Calculating angle to rotate gun towards mouse
        self.player_direction = pygame.math.Vector2(rel_x, rel_y) # Creating a direction vector from player to mouse
        if self.player_direction.length() > 0: 
            self.player_direction = self.player_direction.normalize() 
        
        if -90 < self.angle < 90: 
            self.image = pygame.transform.rotozoom(self.original_image, self.angle, 1) # Rotating gun image to face mouse
        else:
            self.image = pygame.transform.rotozoom(self.original_image, self.angle, 1) 
            self.image = pygame.transform.flip(self.image, False, True) # Flipping gun image vertically for left side
        
        self.rect = self.image.get_rect(center = self.rect.center) # Updating the gun's rectangle after rotation
        self.rect.center = self.player.rect.center + self.player_direction * self.offset_dist # Positioning gun at an offset from player center

class Bullet(pygame.sprite.Sprite):
    def __init__(self, pos, direction, surf, all_sprites, bullet_sprites): # Initializing the Bullet class
        super().__init__() # Calling the parent class's to initialize the child class
        self.image = surf # Setting the bullet's image to the provided surface
        self.rect = self.image.get_rect(center=pos) # Setting the bullet's rectangle centered at the given position
        self.start_pos = pygame.math.Vector2(pos) # Storing the starting position of the bullet
        self.direction = direction # Setting the bullet's movement direction
        self.speed = 1000 # Setting the bullet's speed
        self.z = LAYERS['main'] # Setting the bullet's layer to main
        self.add(all_sprites, bullet_sprites) # Adding the bullet to the provided sprite groups

    def update(self, dt):
        self.rect.center += self.direction * self.speed * dt # Moving the bullet in its direction at its speed
        if (pygame.math.Vector2(self.rect.center) - self.start_pos).length() > 750: # Checking if bullet has traveled beyond 750 pixels
            self.kill() # Removing the bullet 

class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos, player, groups, obstacle_sprites, enemy_name, asset_data, game_ref=None): # Initializing the Enemy class
        super().__init__(groups) # Calling the parent class's to initialize the child class
        self.player = player
        self.enemy_name = enemy_name
        self.asset_data = asset_data
        self.game_ref = game_ref 
        self.status = 'move' # Initial status of the enemy
        
        # Boss Animation Setup 
        if self.enemy_name == 'boss':
            if isinstance(self.asset_data, dict): # Checking if asset_data is a dictionary
                self.frames = self.asset_data.get('move', []) # Start the 'move' animation 
            else: 
                self.frames = self.asset_data 
            self.teleport_timer = pygame.time.get_ticks() # Timer for teleport ability
            self.summon_timer = pygame.time.get_ticks() # Timer for summon ability
        else: 
            self.frames = self.asset_data # All frames for standard enemies
            
        self.frame_index = 0 # Index to track current animation frame
        self.animation_speed = 6 # Speed of animation playback
        
        if self.frames and len(self.frames) > 0: # Checking if frames are available
            self.image = self.frames[0] # Setting the initial image to the first frame
        else:  
            self.image = pygame.Surface((50,50)) # Creating a placeholder surface
            self.image.fill('red') # Filling the placeholder with red color

        self.rect = self.image.get_rect(center=pos) # Setting the enemy's rectangle centered at the given position
        if self.enemy_name == 'boss': self.hitbox = self.rect.inflate(-60, -60) # Larger hitbox for boss
        else: self.hitbox = self.rect.inflate(-20, -20) # Standard hitbox for other enemies
            
        self.speed = random.randint(150, 250) # Random speed for variability
        self.health = 3; self.z = LAYERS['main'] # Setting the enemy's layer to main
        self.obstacle_sprites = obstacle_sprites # Sprites that the enemy can collide with
        self.is_dead = False # Flag to track if the enemy is dead

        # Enemy Stats
        if self.enemy_name == 'bat': self.health = 1; self.speed = 350; self.animation_speed = 12 # Fast bats
        elif self.enemy_name == 'blob': self.health = 6; self.speed = 90  # Slow blobs
        elif self.enemy_name == 'boss': self.health = 100; self.speed = 180; self.animation_speed = 8 # Strong boss
        else: self.health = 3; self.speed = 200 # Medium skeletons
        self.max_health = self.health # Storing max health for health bar calculations

    def move(self, dt): # Enemy movement logic
        if self.is_dead: return # No movement if dead
        current_time = pygame.time.get_ticks() # Getting the current time in milliseconds

        # Boss Logic
        if self.enemy_name == 'boss': 
            if current_time - self.summon_timer > 12000 and self.status == 'move': # 12 second summon cooldown
                self.summon_timer = current_time; self.status = 'summon'; self.frame_index = 0 # Start summon animation 
                return
            dist = pygame.math.Vector2(self.player.rect.center).distance_to(self.rect.center) # Calculating distance to player
            if dist > 400 and current_time - self.teleport_timer > 5000: # 5 second teleport cooldown
                self.teleport_timer = current_time; self.status = 'teleport'; self.frame_index = 0 # Start teleport animation 
                return
            if self.status in ['teleport', 'summon']: # During teleport or summon, do not move
                return
            if dist < 90: # Close range attack
                if self.status != 'attack': self.status = 'attack'; self.frame_index = 0 # Start attack animation
            elif self.status != 'attack': self.status = 'move' # Resume move animation
            if self.status == 'attack': # No movement during attack
                return 
        
        # Standard Movement
        target_vec = pygame.math.Vector2(self.player.rect.center) - pygame.math.Vector2(self.rect.center) # Vector towards player
        if target_vec.length() > 0: direction = target_vec.normalize() # Normalizing to get direction
        else: direction = pygame.math.Vector2() # No movement if on top of player
            
        # Flocking
        if len(self.groups()) > 1: # Checking if enemy is in multiple groups
            mates = self.groups()[1].sprites()  
            if len(mates) > 3: mates = random.sample(mates, 3) # Limiting to 3 random mates for performance
            for sprite in mates:
                if sprite != self and not getattr(sprite, 'is_dead', False): # Avoid self and dead mates
                    dist_vec = pygame.math.Vector2(self.rect.center) - pygame.math.Vector2(sprite.rect.center) # Vector away from mate
                    if 0 < dist_vec.length() < 30: direction += dist_vec.normalize() * 0.8 # Repulsion from close mates

        if direction.length() > 0: direction = direction.normalize() # Normalizing final direction
        self.hitbox.x += direction.x * self.speed * dt # Moving horizontally
        self.collision('horizontal') # Checking horizontal collisions
        self.hitbox.y += direction.y * self.speed * dt # Moving vertically
        self.collision('vertical') # Checking vertical collisions
        self.rect.center = self.hitbox.center # Updating rect position to match hitbox

    def collision(self, direction):
        if direction == 'horizontal': # Horizontal collision detection
            for sprite in self.obstacle_sprites: # Iterating through obstacle sprites
                if 'border' in sprite.obj_name.lower(): # Only checking border obstacles
                    if sprite.hitbox.colliderect(self.hitbox): # Checking for collision
                        if self.hitbox.centerx < sprite.hitbox.centerx: # Collision on the right side
                            self.hitbox.right = sprite.hitbox.left
                        else: self.hitbox.left = sprite.hitbox.right # Collision on the left side
        if direction == 'vertical': # Vertical collision detection
            for sprite in self.obstacle_sprites: # Iterating through obstacle sprites
                if 'border' in sprite.obj_name.lower(): # Only checking border obstacles 
                    if sprite.hitbox.colliderect(self.hitbox): # Checking for collision
                        if self.hitbox.centery < sprite.hitbox.centery: # Collision on the bottom side
                            self.hitbox.bottom = sprite.hitbox.top
                        else: 
                            self.hitbox.top = sprite.hitbox.bottom # Collision on the top side

    def animate(self, dt):
        current_animation = self.frames # Default to all frames
        if self.enemy_name == 'boss' and isinstance(self.asset_data, dict): # Boss with multiple animations
            desired_anim = self.asset_data.get(self.status) # Getting the desired animation based on current status
            if not desired_anim: 
                desired_anim = self.asset_data.get('attack') if self.status == 'summon' else self.asset_data.get('move') # Fallbacks for missing animations
            current_animation = desired_anim # Setting current animation to the desired one
            
        if not current_animation: # No animation frames available
            return
        self.frame_index += self.animation_speed * dt # Advancing the frame index based on animation speed and delta time
        
        if self.frame_index >= len(current_animation): # Checking if the animation has completed
            if self.status == 'teleport': # After teleport animation
                offset = pygame.math.Vector2(random.randint(-300, 300), random.randint(-300, 300)) # Random offset for teleportation
                self.hitbox.center = self.player.hitbox.center + offset # Teleporting near the player
                self.rect.center = self.hitbox.center # Updating rect position
                self.status = 'move' # Resuming move status
            elif self.status == 'summon': # After summon animation
                if self.game_ref:
                    for _ in range(2): self.game_ref.spawn_enemy(forced_type='bat', pos=self.rect.center) # Summoning 2 bats
                    for _ in range(2): self.game_ref.spawn_enemy(forced_type='blob', pos=self.rect.center) # Summoning 2 blobs
                    for _ in range(2): self.game_ref.spawn_enemy(forced_type='skeleton', pos=self.rect.center) # Summoning 2 skeletons
                self.status = 'move' # Resuming move status
            elif self.status == 'attack': self.status = 'move' # Resuming move status after attack
            self.frame_index = 0 # Resetting frame index for looping animations
                
        idx = int(self.frame_index) # Getting the current frame index as an integer
        if idx < len(current_animation): # Ensuring index is within bounds
            self.image = current_animation[idx] # Updating the enemy's image to the current frame
            if self.enemy_name == 'boss': 
                self.image = pygame.transform.scale(self.image, (160, 160)) # Scaling boss image
                self.rect = self.image.get_rect(center=self.hitbox.center) # Updating rect position

    def trigger_death(self):
        self.kill() # Removing the enemy sprite

    def update(self, dt):
        self.move(dt) # Updating enemy movement
        self.animate(dt)  # Updating enemy animation

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups, obstacle_sprites, border_sprites, audio_files, all_sprites, bullet_sprites): # Initializing the Player class
        super().__init__(groups) # Calling the parent class's to initialize the child class
        self.import_assets() # Importing player animation assets
        self.status = 'down' # Initial status of the player
        self.frame_index = 0 # Index to track current animation frame
        self.animation_speed = 8 # Speed of animation playback
        self.all_sprites_ref = all_sprites 
        self.bullet_sprites_ref = bullet_sprites #
        
        if self.animations.get('down'): 
            self.image = self.animations['down'][0] # Setting the initial image to the first frame of 'down' animation
        else: 
            self.image = pygame.Surface((64, 64)); self.image.fill('green') # Placeholder surface if no animation available
        self.rect = self.image.get_rect(center=pos) # Setting the player's rectangle centered at the given position
        self.hitbox = pygame.Rect(0, 0, 26, 26) # Creating a smaller hitbox for the player
        self.hitbox.center = self.rect.center # Aligning hitbox center with player rect center
        self.z = LAYERS['main'] # Setting the player's layer to main
        self.direction = pygame.math.Vector2() # Direction vector for movement
        self.speed = 400 # Player movement speed
        self.obstacle_sprites = obstacle_sprites # Sprites that the player can collide with
        self.border_sprites = border_sprites # Border sprites for collision
        self.can_shoot = True # Flag to track if the player can shoot
        self.can_attack = True # Flag to track if the player can attack
        self.shoot_time = 0 # Timer for shooting cooldown
        self.cooldown = 400 # Shooting cooldown duration in milliseconds
        self.health = 100  # Player health
        self.max_health = 100 # Player max health
        self.vulnerable = True # Flag to track if the player can take damage
        self.hit_time = 0 # Timer for invincibility after being hit
        self.invincibility_duration = 500 # Invincibility duration in milliseconds
        self.shoot_sound = audio_files['shoot'] # Sound effect for shooting
        self.gun = Gun(self, groups) # Creating a Gun instance for the player
        
        bullet_path = join(GUN_PATH, 'bullet.png')
        if exists(bullet_path):
             self.bullet_surf = pygame.image.load(bullet_path).convert_alpha() # Loading the bullet image
        else:
             self.bullet_surf = pygame.Surface((10,10)); self.bullet_surf.fill('yellow') # Placeholder bullet surface

    def damage(self, amount=10): 
        if self.vulnerable:
            self.health -= amount # Reducing player health
            self.vulnerable = False # Setting player to invulnerable
            self.hit_time = pygame.time.get_ticks() # Recording the time of hit

    def heal(self, amount):
        self.health += amount # Increasing player health
        if self.health > self.max_health: self.health = self.max_health # Capping health at max health [Cannot exceed max health]

    def check_death(self): 
        if self.health <= 0: # Checking if player health is zero or below
            self.gun.kill() # Removing the gun sprite
            self.kill() # Removing the player sprite

    def import_assets(self):
        self.animations = {'up': [], 'down': [], 'left': [], 'right': []} # Initializing animation dictionary
        path = PLAYER_PATH  # Base path for player animations
        if not exists(path): 
            return
        for animation in self.animations.keys():
            full_path = join(path, animation) # Full path to the specific animation folder
            self.animations[animation] = import_folder(full_path) # Importing frames for the animation

    def face_mouse(self):
        screen_w, screen_h = pygame.display.get_surface().get_size() # Getting the screen dimensions
        mouse_x, mouse_y = pygame.mouse.get_pos() # Getting the current mouse position
        rel_x = mouse_x - screen_w // 2 # Relative x from screen center to mouse
        rel_y = mouse_y - screen_h // 2 # Relative y from screen center to mouse
        angle = math.degrees(math.atan2(rel_y, rel_x)) # Calculating angle to mouse
        if -45 < angle <= 45: 
            self.status = 'right' # Facing right
        elif 45 < angle <= 135: 
            self.status = 'down' # Facing down
        elif -135 < angle <= -45: 
            self.status = 'up' # Facing up
        else: 
            self.status = 'left' # Facing left

    def input(self):
        keys = pygame.key.get_pressed() # Getting the current state of all keyboard keys
        if keys[pygame.K_UP] or keys[pygame.K_w]: # Checking for upward movement keys
            self.direction.y = -1 # Moving up
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]: # Checking for downward movement keys
            self.direction.y = 1 # Moving down
        else: 
            self.direction.y = 0 # No vertical movement
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: # Checking for rightward movement keys 
            self.direction.x = 1 # Moving right
        elif keys[pygame.K_LEFT] or keys[pygame.K_a]: # Checking for leftward movement keys
            self.direction.x = -1 # Moving left
        else: self.direction.x = 0 # No horizontal movement
        self.face_mouse() # Updating player facing direction based on mouse position
        if pygame.mouse.get_pressed()[0] and self.can_shoot and self.can_attack: # Checking for left mouse button press and shooting ability
            self.shoot() # Calling the shoot method
            self.can_shoot = False # Setting can_shoot to False to enforce cooldown
            self.shoot_time = pygame.time.get_ticks() # Recording the time of shooting

    def shoot(self):
        if self.shoot_sound: self.shoot_sound.play() # Playing shooting sound effect
        direction = self.gun.player_direction # Getting the direction the gun is facing
        pos = self.gun.rect.center + direction * 30 # Positioning bullet at the gun's muzzle
        Bullet(pos, direction, self.bullet_surf, self.all_sprites_ref, self.bullet_sprites_ref) # Creating a Bullet instance

    def move(self, dt):
        if self.direction.length() > 0: # Checking if there is any movement input
            self.direction = self.direction.normalize() # Normalizing direction vector for consistent speed
        self.hitbox.x += self.direction.x * self.speed * dt # Moving horizontally
        self.collision('horizontal') # Checking horizontal collisions
        self.hitbox.y += self.direction.y * self.speed * dt # Moving vertically
        self.collision('vertical') # Checking vertical collisions
        self.rect.center = self.hitbox.center # Updating rect position to match hitbox

    def collision(self, direction): # Collision detection and response
        all_obstacles = list(self.obstacle_sprites) + list(self.border_sprites) # Combining obstacle and border sprites
        if direction == 'horizontal': # Horizontal collision detection
            for sprite in all_obstacles: # Iterating through all obstacle sprites 
                if sprite.hitbox.colliderect(self.hitbox): # Checking for collision
                    if self.direction.x > 0: # Moving right
                        self.hitbox.right = sprite.hitbox.left # Adjusting hitbox position to prevent overlap
                    if self.direction.x < 0: # Moving left
                        self.hitbox.left = sprite.hitbox.right # Adjusting hitbox position to prevent overlap
        if direction == 'vertical': # Vertical collision detection
            for sprite in all_obstacles: # Iterating through all obstacle sprites
                if sprite.hitbox.colliderect(self.hitbox): # Checking for collision
                    if self.direction.y > 0: # Moving down
                        self.hitbox.bottom = sprite.hitbox.top # Adjusting hitbox position to prevent overlap
                    if self.direction.y < 0: # Moving up
                        self.hitbox.top = sprite.hitbox.bottom # Adjusting hitbox position to prevent overlap

    def animate(self, dt):
        if self.direction.length() == 0: # No movement input
            self.frame_index = 0 # Resetting frame index to first frame
            if self.animations[self.status]: # Checking if animation frames exist for current status
                self.image = self.animations[self.status][int(self.frame_index)] # Setting image to first frame of current status
            return
        self.frame_index += self.animation_speed * dt # Advancing the frame index based on animation speed and delta time
        current_anim = self.animations[self.status] # Getting the current animation frames based on player status
        if current_anim:
            if self.frame_index >= len(current_anim): self.frame_index = 0 # Looping the animation
            self.image = current_anim[int(self.frame_index)] # Updating the player's image to the current frame

    def cooldowns(self):
        current_time = pygame.time.get_ticks() # Getting the current time in milliseconds
        if not self.can_shoot:
            if current_time - self.shoot_time >= self.cooldown: # Checking if shooting cooldown has passed
                self.can_shoot = True # Resetting shooting ability after cooldown
        if not self.vulnerable:
            if current_time - self.hit_time >= self.invincibility_duration: # Checking if invincibility duration has passed 
                self.vulnerable = True # Resetting vulnerability after invincibility duration

    def update(self, dt): # Updating player state
        self.input() # Handling player input
        self.cooldowns() # Managing cooldowns
        self.move(dt) # Updating player movement
        self.animate(dt) # Updating player animation
        self.check_death() # Checking for player death