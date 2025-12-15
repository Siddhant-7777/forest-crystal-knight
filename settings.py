# IMPORTS
import os 
from os.path import join

# WINDOW SETTINGS
WINDOW_WIDTH, WINDOW_HEIGHT = 1280, 720
FPS = 60
TILE_SIZE = 64 # Size of each tile in the game world [64x64 pixels]

# LAYERS
LAYERS = {
    'ground': 0,
    'main': 1,
    'top': 2
}

# COLORS
BG_COLOR = '#3a7d44'   
UI_BG_COLOR = (0, 0, 0, 180) 

# PATHS
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # Creating a variable to store the base directory path
ASSETS_DIR = join(BASE_DIR, 'assets') # Using BASE_DIR to create ASSETS_DIR variable [Assets Directory]

PLAYER_PATH = join(ASSETS_DIR, 'images', 'player')
ENEMY_PATH = join(ASSETS_DIR, 'images', 'enemies')
GUN_PATH = join(ASSETS_DIR, 'images', 'gun')
MAP_PATH = join(ASSETS_DIR, 'data', 'maps', 'world.tmx') # Blueprint for the game map, only contains data [Coordinates, object placements]
TREE_PATH = join(ASSETS_DIR, 'data', 'graphics', 'objects', 'green_tree.png') # For game boundary 
AUDIO_PATH = join(ASSETS_DIR, 'audio')