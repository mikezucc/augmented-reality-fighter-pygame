"""
Copyright 2009, 2010, 2011 Leif Theden

This file is part of Fighter Framework.

Fighter Framework (FF) is free software: you can redistribute it
and/or modify it under the terms of the GNU General Public License
as published by the Free Software Foundation, either version 3 of
the License, or (at your option) any later version.

FF is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with FF.  If not, see <http://www.gnu.org/licenses/>.
"""

import game
from pygame.sprite import DirtySprite, LayeredUpdates, RenderUpdates
from pygame.rect   import Rect

from pygame.transform import scale
import pygame, os.path

"""
loading images
converting for good blits
caching stuff
managing the screen
managing screen buffers
"""

DEBUG = False

def debug(text):
    if DEBUG: sys.stdout.write(text)


DOUBLE_SIZE = True
DRAW_COLLISION_BOXES = False

image_cache      = []
image_path_cache = {}

screen = None

def setup_display():
    global screen
    global screen_buffer

    pygame.display.set_caption("IK Fighter")

    if DOUBLE_SIZE:
        screen = pygame.display.set_mode((644, 406))
        screen_buffer = pygame.Surface((322, 203))
        screen_buffer.convert(screen)
    else:
        screen = pygame.display.set_mode((322, 203))

def set_background(surface):
    global screen
    global screen_buffer

    if DOUBLE_SIZE:
        screen_buffer.blit(surface, (0,0))
    else:
        screen.blit(surface, (0,0))

# return a surface for drawing onto the window
def get_display():
    if DOUBLE_SIZE:
        return screen_buffer
    else:
        return screen

def add_image_to_cache(image, fullpath=None):
    global image_cache
    global image_path_cache

    image_cache.append(image)
    if fullpath != None:
        image_path_cache[fullpath] = image_cache.index(image)

# we can pass an image here to see if there is something
# like it already in memory

# cache lookups don't work
def get_image_from_cache(fullpath=None, image=None):
    global image_cache
    global image_path_cache

    try:
        return image_cache[image_path_cache[fullpath]]
    except KeyError:
        pass

    # only way i know how to compare images.  ok?
    if image != None:
        for cached_image in image_cache:
            if cached_image == image:
                print "from cache"
                return cached_image

    return None

# images are not "converted" here, make sure it happens at some point
def load_image(name, use_cache=True):
    global image_cache

    fullpath = os.path.realpath(os.path.join(game.resource_path,name))

    if use_cache:
        image = get_image_from_cache(fullpath)
        if image != None: return image, image.get_rect()

    try:
        image = pygame.image.load(fullpath)
    except pygame.error, message:
        print 'Cannot load image:', name
        raise SystemExit, message

    if use_cache:
        add_image_to_cache(image, fullpath)

    return image, image.get_rect()

def load_image_with_alpha(name, use_cache=True):
    image, rect = load_image(name, use_cache)
    image = image.convert_alpha()
    return image, rect

def load_image_with_colorkey(name, use_cache=True):
    image, rect = load_image(name, use_cache)
    image = image.convert()

    # by default, use the color at the upper left corner at the colorkey
    image.set_colorkey(image.get_at((0,0)))

    return image, rect

def update_display():
    if DOUBLE_SIZE:
        #group.clear(screen_buffer, background)
        #dirty = group.draw(screen_buffer)
        scale(screen_buffer, (644, 406), screen)
        #pygame.transform.scale2x(screen_buffer, screen)

    pygame.display.update()

def draw(background):
    global screen
    global screen_buffer

    if DOUBLE_SIZE:
        group.clear(screen_buffer, background)
        dirty = group.draw(screen_buffer)
        #pygame.transform.scale(screen_buffer, (644, 406), screen)
        pygame.transform.scale2x(screen_buffer, screen)
        pygame.display.update()
    else:
        # clear the dirty rects
        group.clear(screen, background)

        # draw new graphics, keep a list of dirty rects
        dirty = group.draw(screen)

        # Render the text for fps
        #fps_font = pygame.font.Font(None, 24)
        #text = fps_font.render('fps %d' % global_clock.get_fps(), True, (255,
        #255, 255), (0,0,0))
        #textRect = text.get_rect()
        #textRect.topleft = (0,0)
        # Blit the text
        #surface.blit(text, textRect)
        #dirty.append(textRect)

        # flip or something
        #pygame.display.update(dirty)
        pygame.display.update()
