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

"""=====================================================================
Basically anything relating to the games "engine" goes here:
Animation
Handling input
Handling the display, sounds, etc

normally, use milliseconds to advance frames, but...
using that means that faster computers will perform differently than
slower ones...mostly concerned about collisions missed if frames are
skipped.  so, to make it consistent, use something like mugen...
"gameticks"...

an experimental zooming method was tried, not used

====================================================================="""

# syncing the engine to the view might be a good idea, since we are
# dealing with a game that is very dependant on animations

# pygame has some good utilities unrelated to graphics/sound
import pygame, os, time
from pygame.time import Clock
from pygame.locals import *
from pygame.sprite import RenderUpdates
from pygame.rect import Rect

import sound, gfx
from states import StateDriver
from buttons import *

from pygame.transform import smoothscale as scale
from pygame.draw import rect as draw_rect

from time import time as ms

import sys, gc

DRAW_DEBUG = False

# SYSTEM CONSTANTS
GAMESPEED = .02             # HOW MANY SECONDS PER GAME FRAME
MAX_FRAMES_PER_CYCLE = 4    # MAXIMUM FRAMES COMPUTED PER CYCLE
# above currently not implemented properly

# random globals, because i just can't be bothered to care
global_clock            = Clock()

DEFAULT_CPU_DIFFICULTY = 50
CPU_VS_CPU_DIFFICULTY  = 95

p1_key_def = {
    K_e: BUTTON_HI_KICK,
    K_w: BUTTON_MED_KICK,
    K_q: BUTTON_LOW_KICK,
    K_a: BUTTON_LOW_PUNCH,
    K_s: BUTTON_MED_PUNCH,
    K_d: BUTTON_HI_PUNCH,
    K_LEFT: BUTTON_LEFT,
    K_RIGHT: BUTTON_RIGHT,
    K_DOWN: BUTTON_DOWN,
    K_UP: BUTTON_UP
}

p2_key_def = {
    K_KP_MINUS: BUTTON_HI_KICK,
    K_KP_PLUS: BUTTON_MED_KICK,
    K_KP_ENTER: BUTTON_LOW_KICK,
    K_KP_DIVIDE: BUTTON_LOW_PUNCH,
    K_KP_MULTIPLY: BUTTON_MED_PUNCH,
    K_KP_PERIOD: BUTTON_HI_PUNCH,
    K_KP4: BUTTON_LEFT,
    K_KP6: BUTTON_RIGHT,
    K_KP5: BUTTON_DOWN,
    K_KP8: BUTTON_UP
}

def init():
    try:
        pygame.display.init()
    except pygame.error:
        print "display cannot initialize, cannot continue"
        sys.exit()

    gfx.setup_display()
  
    try:
        pygame.mixer.init()
    except pygame.error:
        print "cannot initialize pygame sound mixer."
        print "sound and music will not work."

    # block mouse events to keep them from filling event buffer
    pygame.event.set_blocked(pygame.MOUSEMOTION)

def debug(text):
    sys.stdout.write(text)
    pass

class Arena(object):
    def __init__(self, floor, height, width, image):
        self.image  = image
        self.floor  = floor
        self.height = height
        self.width  = width

class UpdateableObject(object):
    def update(self, time):
        pass

    def enable(self):
        self._is_enabled = True

    def disable(self):
        self._is_enabled = False

class DrawableObject(UpdateableObject):
    def __init__(self):
        super(DrawableObject, self).__init__()
        self._is_visible = False
        self._is_enabled = False
        self.dirty = False

    # return a rect
    def draw(self, surface):
        raise NotImplementedError, self

    def show(self):
        self.is_visible = True
        # tell our manager?

    def hide(self):
        self._is_visible = False

class KeyableObject(object):
    def __init__(self, keys=None):
        """keys is a list of keys that this will respond to.
        If None, it listens to everything"""
        self.keys = keys

    def mask_event(self, key, unicode, pressed):
        if self.keys:
            if key not in self.keys:
                return
        self.key_event(key, unicode, pressed)

    def keyEvent(self,key,unicode, pressed):
        raise SubclassShouldImplement

# this class should [eventually] check for values that are out of the
# range of python's built in types.  b/c they will eventually crash the
# program is left running too long.
class Timer(UpdateableObject):
    def __init__(self, alarm=None):
        self._alarm = alarm
        self.reset()

    def update(self, time):
        self.value += time

    def reset(self):
        self.value = 0.0

    #@property
    def get_alarm(self):
        return self._alarm

    #@alarm.setter
    def set_alarm(self, alarm):
        self._alarm = alarm
        self.value = 0.0

    alarm = property(get_alarm, set_alarm)

    @property
    def finished(self):
        if self.alarm != None:
            return self.value >= self.alarm
        else:
            return True

class CallbackTimer(Timer):
    def __init__(self, alarm=None, callback=None, args=[]):
        super(CallbackTimer, self).__init__(alarm)
        self.callback = (callback, args)

    def update(self, time):
        self.value += time

        if self.finished:
            self.callback[0](*self.callback[1])
            return False

# worlds will go on, even if nobody is watching.  (no camera/views)
class World(object):
    def __init__(self, extent):
        self._drawables = []
        self._updateables = []
        self._extent = Rect((0,0), extent)

    #@property
    def get_extent(self):
        return self._extent

    #@extent.setter
    def set_extent(self, extent):
        self._extent = extent

    extent=property(get_extent, set_extent)

    @property
    def drawables(self):
        return self._drawables[:]

    def add(self, obj):
        if isinstance(obj, DrawableObject):
            self._drawables.append(obj)
            self._updateables.append(obj)
        elif isinstance(obj, UpdateableObject):
            self._updateables.append(obj)

    def remove(self, obj):
        try:
            self._drawables.remove(obj)
        except (IndexError, ValueError):
            pass

        try:
            self._updateables.remove(obj)
        except (IndexError, ValueError):
            pass

        #gc.collect()
        #print self, obj
        #for obj in gc.get_referrers(obj):
        #   print "  ", type(obj), id(obj)

    def update(self, time):
        to_remove = []
        [ to_remove.append(obj) for obj in self._updateables \
        if obj.update(time) == False ]
        [ self.remove(obj) for obj in to_remove ]


class Renderer(UpdateableObject):
    """
    Kinda like a sprite group.  renders a scene to a surface.
    """

    def __init__(self):
        self.lostsprites = []
        self.blitdict = {}
        self.zoom = 1
        self.scratch_surface = pygame.Surface((0,0))
        self.use_zoom = False
        self.background = None
        self.redraw = False

    def set_background(self, image):
        self.background = image
        self.redraw = True

    def clear(self, surface):
        bgd = self.background
        try:
            bgd.__call__
        except AttributeError:
            pass
        else:
            for r in self.lostsprites:
                bgd(surface, r)
            for r in self.blitdict.values():
                if r is not 0: bgd(surface, r)
            return
        surface_blit = surface.blit
        for r in self.lostsprites:
            surface_blit(bgd, r, r)
        for r in self.blitdict.values():
            if r is not 0:
                if isinstance(r, list):
                    for r2 in r:
                        surface_blit(bgd, r2, r2)
                else:
                    surface_blit(bgd, r, r)

    # this is called on the first time of a draw
    # sets a buffer for zooming, and converts the frame for the
    # surface to be blitted, then sets draw to the normal func
    def draw(self, surface):
        self.scratch_surface = pygame.Surface(surface.get_size())
        self.scratch_surface.convert(surface)
        self.draw = self.real_draw
        return self.draw(surface)

    def real_draw(self, surface):

        if self.redraw:
            surface.blit(self.background, (0,0))
            self.redraw = False

        # dirty rects method
        if self.background != None:
            self.clear(surface)

        to_remove = []
        dirty = []

        blitdict = self.blitdict
        dirty_append = dirty.append

        for obj in self.drawables:
            newrect = obj.draw(surface)

            # drawing somehow failed, just remove it from things to draw
            if newrect == None:
                to_remove.append(obj)

            # some objects handle their own rendering (like menus) and return a list
            elif isinstance(newrect, list):
                try:
                    r = blitdict[obj]
                except KeyError:
                    dirty.extend(newrect)
                else:
                    for x in range(len(r)):
                        if newrect[x].colliderect(r[x]):
                            dirty_append(r[x].union(r[x]))
                        else:
                            dirty_append(r[x])
                blitdict[obj] = newrect

            # normal sprites are handled here
            else:
                try:
                    r = blitdict[obj]
                except KeyError:
                    dirty_append(newrect)
                else:
                    if newrect.colliderect(r):
                        dirty_append(newrect.union(r))
                    else:
                        dirty_append(newrect)
                        dirty_append(r)
                blitdict[obj] = newrect

        # remove the sprites that cause us problems
        # ...i mean PUNISH them.
        for obj in to_remove:
            self.world.remove(obj)
            try:
                # unless we kill this ref, a sprite won't be gc'd
                del self.blitdict[obj]
            except:
                pass

        self.lostsprites = dirty
        return dirty

    def zoom_draw(self, surface):
        to_remove = []
            
        #lazy
        #self.scratch_surface.blit(self.background, (0,0))
        #self.scratch_surface.fill((20,0,100))
        #surface.fill((20,20,20))

        # dirty rects are wrong here, because they are not scaled

        # TODO: this should be a list of visible objects, not just all objects
        for obj in self.drawables:
            try:
                newrect = obj.draw(self.scratch_surface)
            except:
                to_remove.append(obj)
                continue

            # some objects handle their own rendering (like menus) and return a list
            if isinstance(newrect, list):
                try:
                    r = blitdict[obj]
                except:
                    # no dict for this object add the the rects to dirty
                    [ dirty_append(subrect) for subrect in newrect ]
                else:
                    for x in range(len(r)):
                        if newrect[x].colliderect(r[x]):
                            dirty_append(r[x].union(r[x]))
                        else:
                            dirty_append(r[x])
                blitdict[obj] = newrect

            else:
                try:
                    r = blitdict[obj]
                except KeyError:
                    dirty_append(newrect)
                else:
                    if newrect.colliderect(r):
                        dirty_append(newrect.union(r))
                    else:
                        dirty_append(newrect)
                        dirty_append(r)
                blitdict[obj] = newrect

        #x,y = surface.get_size()

        #width  = x
        #height = y / self.aspect * 2

        #print "w,h:", width, height

        #print x,y, self.extent.width
        #y = (y / 2) - (height / 2)
        #print x,y, self.extent.size
        #print self.extent
        #draw_rect(self.scratch_surface, (255,255,255), self.extent, 2)
        #zoom_surface = pygame.Surface(self.extent.size)
        #zoom_surface.blit(self.scratch_surface, (0,0), area=self.extent)
        #width_int = int(width)
        #height_int = int(height)
        #zoom2 = scale(zoom_surface, (width_int, height_int))
        #y = self.scratch_surface.get_size()[1]
        #y = self.extent.top / 2
        #surface.blit(zoom2, (0,y))
        #zoom_surface = pygame.Surface((x,y))
        #zoom_surface.blit(self.scratch_surface, (0,0))
        #zoom2 = scale(zoom_surface, (width, y))
        #surface.blit(zoom2, (0,0))

        surface.blit(self.scratch_surface, (0,0))

        # remove the sprites that cause us problems
        # ...i mean PUNISH them.
        for obj in to_remove:
            self.world.remove(obj)
            try:
                # unless we kill this ref, a sprite won't be gc'd
                del self.blitdict[obj]
            except:
                pass

        return dirty

class View(Renderer):
    def __init__(self, world, extent=None):
        super(View, self).__init__()
        self.extent_timer = Timer()
        self.zoom_timer = Timer()
        self.extent_timer2 = Timer()

        self.world = world
        self.zoom_obj = None

        if extent == None:
            self.extent = world.extent.copy()

        self.target_extent = self.extent

        self.dampening = .01
        self.zoom = 1
        self.zoom_padding = 70

        self.aspect = float(self.extent.width) / self.extent.height

    @property
    def drawables(self):
        return self.world.drawables

    def update(self, time):
        if self.zoom_obj != None:
            self.extent_timer.update(time)
            self.extent_timer2.update(time)
            self.zoom_timer.update(time)

            if self.extent_timer.finished:
                rects = [ obj.rect for obj in self.zoom_obj ]
                extent = rects[0].unionall(rects[1:])
                extent.inflate_ip(self.zoom_padding, self.zoom_padding)

                target_zoom = float(self.world.extent.width) / extent.width

                old_width  = float(extent.width)
                new_width = float(self.world.extent.width) / self.zoom

                NEW_width  = float(extent.width)

                if new_width > old_width:
                    extent.inflate_ip(new_width - old_width, 0)
                elif new_width < old_width:
                    extent.inflate_ip(0-(old_width - new_width), 0)

                self.aspect = float(extent.width) / extent.height
                self.target_extent = extent
                self.extent.size = extent.size
                self.scratch_surface.set_clip(extent)
                self.target_zoom = round(target_zoom, 2)

                self.extent_timer.alarm = 100.000 / 1000.000

            if self.extent_timer2.finished:

                centerx = self.extent.centerx
                centery = self.extent.centery

                #print self.extent, self.target_extent

                if centerx > self.target_extent.centerx:
                    self.extent.left -= 1                   
                elif centerx < self.target_extent.centerx:
                    self.extent.left += 1

                if centery > self.target_extent.centery:
                    self.extent.top -= 1
                elif centery < self.target_extent.centery:
                    self.extent.top += 1
                
                self.scratch_surface.set_clip(self.extent)

                                
                # we don't have a new extent, but lets adjust
                # the current extent to match the target one.
                #extent = self.target_extent
                #self.extent = extent
                #self.aspect = float(extent.width) / extent.height
                #self.scratch_surface.set_clip(extent)
                #self.target_zoom = round(target_zoom, 2)

                # a way of smoothing out the panning without a ton of maths
                d = abs(self.extent.centerx - self.target_extent.centerx)
                if d >= 17:
                    delay = 10
                elif d == 0:
                    delay = 100
                else:
                    delay =  60 - (60 * (d/20.0))

                #print d
                #print d, delay

                self.extent_timer2.alarm = delay / 1000.0

            return
            if self.zoom_timer.finished:
                if self.target_zoom > self.zoom:
                    #print self.target_zoom, self.zoom, self.extent.width, "gt"
                    self.zoom += self.dampening
                    old_width = float(self.extent.width)
                    new_width = float(self.world.extent.width) / self.zoom
                    self.extent.inflate_ip(new_width - old_width, 0)
                    self.aspect = float(self.extent.width) / self.extent.height

                elif self.target_zoom <= self.zoom - self.dampening:
                    #print self.target_zoom, self.zoom, self.extent.width, "lt"
                    self.zoom -= self.dampening
                    old_width = float(self.extent.width)
                    new_width = float(self.world.extent.width) / self.zoom
                    self.extent.inflate_ip(0-(old_width - new_width), 0)
                    self.aspect = float(self.extent.width) / self.extent.height

                self.zoom_timer.alarm = 20.000 / 1000.000


    def set_zoom_objects(self, obj_list):
        if isinstance(obj_list, list):
            rects = [ obj.rect for obj in obj_list ]
            width = rects[0].unionall(rects[1:]).width
            zoom = float(self.world.extent.width) / width
            self.extent = self.world.extent.copy()
            self.aspect = float(self.extent.width) / self.extent.height
            self.zoom_obj = obj_list
            self.target_zoom = round(zoom, 2)
            self.extent_timer.alarm = 90.000 / 1000.000
            self.zoom_timer.alarm = 30.000 / 1000.000

# helpful little class whose dimensions are the the surface passed to it
# includes a basic view for drawing.
class StaticWorld(World):
    def __init__(self, extent):
        super(StaticWorld, self).__init__(extent)
        self.view = View(self)
        self._super_update = super(StaticWorld, self).update

    def update(self, time):
        self._super_update(time)
        self.view.update(time)

    def draw(self, surface):
        self.view.draw(surface)

# translate pygame imputs into game inputs
class MappedInput(object):
    def __init__(self, puppet, key_def):
        self.puppet = puppet
        self.key_def = key_def

    # return the state the fighter *would* change to
    def handle_key(self, key0, pressed):
        for key1, cmd in self.key_def.items():
            if key0 == key1:
                return self.puppet.handle_command(cmd, pressed)
        return False

    def play_key(self, key0, pressed):
        for key1, cmd in self.key_def.items():
            if key0 == key1:
                self.puppet.play_command(cmd, pressed)
