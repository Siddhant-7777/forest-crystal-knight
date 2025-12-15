import pygame
from settings import *
from sprites import Player

class CameraGroup(pygame.sprite.Group): # Creating a class named CamerGroup that inherits from pygame.sprite.Group
    def __init__(self): # Initializing the class (start-up)   
        super().__init__()  # Calling the parent class's to initialize the child class
        self.display_surface = pygame.display.get_surface() # Storing the main display surface in a variable
        self.offset = pygame.math.Vector2() # Creating a vector to store the shifted values for camera movement
     
        # Map limits
        self.map_width = 0 
        self.map_height = 0
        self.ui_font = pygame.font.SysFont("arial", 18, bold=True) 

    def set_map_limits(self, width, height):
        self.map_width = width # 3328 
        self.map_height = height # 3200 
    
    def custom_draw(self, player):
        screen_w, screen_h = self.display_surface.get_size()
        
        # Offset = Player's Real Position - Center of Screen
        self.offset.x = player.rect.centerx - screen_w // 2 # Determining the center x-coordinate of the player relative to the screen center 
        self.offset.y = player.rect.centery - screen_h // 2 # Determining the center y-coordinate of the player relative to the screen center

 # Preventing camera from moving beyond map boundaries
        # Left Boundary
        if self.offset.x < 0: 
            self.offset.x = 0 
        # Top Boundary
        if self.offset.y < 0: 
            self.offset.y = 0
        # Right Boundary
        if self.offset.x > self.map_width - screen_w: 
            self.offset.x = self.map_width - screen_w
        # Bottom Boundary
        if self.offset.y > self.map_height - screen_h: 
            self.offset.y = self.map_height - screen_h

        self.display_surface.fill(BG_COLOR)

        # 1. Draw Ground
        for sprite in self.sprites(): # Iterating through all sprites in the group
            if sprite.z == LAYERS['ground']: # Selecting only ground layer sprites for drawing
                offset_pos = sprite.rect.topleft - self.offset # Calculating the position to draw
                if -100 < offset_pos.x < screen_w + 100 and -100 < offset_pos.y < screen_h + 100: # Culling: Only drawing if within screen bounds [with a buffer of 100 pixels, lowers rendering & improves fps]
                    self.display_surface.blit(sprite.image, offset_pos) # Drawing the sprite on the display surface at the calculated position [blitt = drawing]

        # 2. Draw Main Sprites
        main_sprites = [] # List to hold main layer sprites
        for s in self.sprites(): # Iterating through all sprites in the group
            if s.z == LAYERS['main']: # Selecting only main layer sprites for drawing
                main_sprites.append(s) # Adding the sprite to the main_sprites list 

        def get_y_position(sprite): 
            return sprite.rect.centery # Returning the center y-coordinate of the sprite's rectangle
        sorted_sprites = sorted(main_sprites, key=get_y_position) # Sorting the main sprites based on their y-coordinate to ensure correct layering (sprites lower on the screen are drawn last)


        for sprite in sorted_sprites: 
            offset_pos = sprite.rect.topleft - self.offset  # Calculating the position to draw (converting world coordinates to screen coordinates)
            
            if -100 < offset_pos. x < screen_w + 100 and -100 < offset_pos.y < screen_h + 100: # Culling: Only drawing if within screen bounds [with a buffer of 100 pixels, lowers rendering & improves fps]
                self.display_surface.blit(sprite.image, offset_pos) # Drawing the sprite on the display surface at the calculated position

                # Mob Health Bar
                if hasattr(sprite, 'enemy_name') and sprite.enemy_name != 'boss': # Checking if the sprite has an 'enemy_name' attribute (indicating it's an enemy) and is not a boss 
                    # a. Calculating Health Percentage
                    current_hp = sprite.health 
                    max_hp = sprite.max_health 
                    health_percentage = current_hp / max_hp

                    # b. Deciding where to draw the bar
                    bar_x = offset_pos.x # Align with left side of enemy
                    bar_y = offset_pos.y - 10 # 10 pixels ABOVE the enemy's head
                    bar_w = sprite.rect.width # Same width as the enemy
                    bar_h = 4 # 4 pixels tall

                    # c. Drawing the Black Background
                    bg_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
                    pygame.draw.rect(self.display_surface, 'black', bg_rect)

                    # d. Drawing the Red Health 
                    current_health_width = bar_w * health_percentage 
                    
                    health_rect = pygame.Rect(bar_x, bar_y, current_health_width, bar_h)
                    pygame.draw.rect(self.display_surface, 'red', health_rect)
        
        # 3. Draw Top Layer
        for sprite in self.sprites(): # Iterating through all sprites in the group
            if sprite.z == LAYERS['top']: # Selecting only top layer sprites for drawing
                 offset_pos = sprite.rect.topleft - self.offset # Calculating the position to draw
                 self.display_surface.blit(sprite.image, offset_pos) # Drawing the sprite on the display surface at the calculated position

