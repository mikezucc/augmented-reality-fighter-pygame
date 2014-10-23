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

import sound, gfx
import pygame

SOUND_PLAY  = 0
SOUND_HIT   = 1
SOUND_MISS  = 2
SOUND_BLOCK = 3

class CollisionBox(pygame.Rect):
    def __init__(self, *arg):
        super(CollisionBox, self).__init__(*arg)
        self.parent = None

class AnimationFrame(object):
    def __init__(self, image=None):
        self.parent = None
        self.name = None
        
        if image == None:
            self.image = None
            self.rect = None
        else:
            self.image = image
            self.rect  = image.get_rect()

        self.ttl         = 0        # how many ms until flipped to next (-1 = never)
        self.move_avatar = (0,0)    # this frame will move the avatar
        self.axis        = (0,0)    # where images are aligned (usually at bottom)
        self.facing      = 0        # 0 = left, 1 = right

        self.sound       = sound.dummy  # sound played regardless of hit or miss

    def __del__(self):
        print "dying frame", id(self)

    def cleanup(self):
        self.__dict__ = {}

    # only handle x, currently
    def flip(self):
        width = self.rect.width

        # flip image
        self.image = pygame.transform.flip(self.image, 1, 0)

        # move the fighter to compensate the axis change
        #y = self.parent.parent.parent.position[1]
        #self.parent.parent.parent.set_position((self.rect.left - axis[0], y))

        axis = list(self.axis)

        # flip the axis
        axis[0] = width - self.axis[0]
        self.axis = tuple(axis)

        # reverse move_avatar
        mv = list(self.move_avatar)
        if mv[0] > 0:
            mv[0] = 0 - mv[0]
        else:
            mv[0] = abs(mv[0])
        self.move_avatar = tuple(mv)

    # return True if we needed to flip this.  also, means we just updated
    def face(self, d):
        if self.facing != d:
            self.facing = d
            self.flip()
            self.update(self.parent.parent.position)
            return True
        else:
            return False

    # update the hit boxes and rect position from axis
    def update(self, axis):
        self.rect.topleft = self.adjust_position(axis)

    # compute the rect's upper left corner when adjusted for the axis
    def adjust_position(self, position):
        new_pos = (position[0] - self.axis[0], position[1] - self.axis[1])
        return new_pos

    def load_image(self, filename):
        self.image, self.rect = gfx.load_image(filename)

    def load_sound(self, filename, sound_type=SOUND_PLAY):
        this_sound = sound.load_sound(filename)
        self.sound = this_sound

    def __str__(self):
        return "AnimFrame \"%s\"" % id(self)

class FighterFrame(AnimationFrame):
    """
    A class that contains an image along with hitboxes and some control features.

    These are more feature rich and are used with a fighter.  Each frame of an animation
    can contain any number of hitboxes, damage boxes (area that can be attacked) and
    block boxes (area that be be blocked with).  Sounds can also be attached to the frame
    to be played with it is displayed.
    """

    def __init__(self):
        super(FighterFrame, self).__init__()
        # org = origin; where the topleft corner of the hb is
        self.block_box_org = [] # block box ORIGIN! (x,y)
        self.hit_box_org = []   # hit box ORIGIN! (x,y)
        self.dmg_box_org = []   # dmg box ORIGIN! (x,y)

        self.hit_box = []       # these are updated when position changes
        self.dmg_box = []       # contain a pygame rect
        self.block_box = []     # these are updated when position changes

        self.pause       = True     # allows the animation to pause/or not
        self.hold        = False    # frames won't advance while key is being held

        # dummy sounds simplify checking at runtime
        self.sound_block = sound.dummy  # play a sound when attack is blocked
        self.sound_miss  = sound.dummy  # play a sound when frame is displayed, no hit
        self.sound_hit   = sound.dummy  # hit a collision is detected

        # spawn lots of stuff
        self.hit_spawn   = None # spawn something if hit
        self.block_spawn = None # if a hit lands, but is blocked or not valid

    def add_collision_box(self, rect, ol, l):
        rect.parent = self
        ol.append(list(rect.topleft))
        l.append(rect)

    def add_dmg_box(self, rect):
        self.add_collision_box(rect, self.dmg_box_org, self.dmg_box)

    def add_hit_box(self, rect):
        self.add_collision_box(rect, self.hit_box_org, self.hit_box)

    def add_block_box(self, rect):
        self.add_collision_box(rect, self.block_box_org, self.block_box)

    # only handle x, currently
    def flip(self):
        width = self.rect.width

        # flip image
        self.image = pygame.transform.flip(self.image, 1, 0)

        # move the fighter to compensate the axis change
        #y = self.parent.parent.parent.position[1]
        #self.parent.parent.parent.set_position((self.rect.left - axis[0], y))

        axis = list(self.axis)

        diff = (width - axis[0]) - axis[0]

        # flip the damage boxes
        for origin, box in zip(self.dmg_box_org, self.dmg_box):
            right = origin[0] + box.width
            if origin[0] < axis[0]:
                origin[0] = right + ((axis[0] - right)*2) + diff
            else:
                origin[0] = right - ((right - axis[0])*2) + diff

        # flip the hit boxes
        for origin, box in zip(self.hit_box_org, self.hit_box):
            right = origin[0] + box.width
            if origin[0] < axis[0]:
                origin[0] = right + ((axis[0] - right)*2) + diff
            else:
                origin[0] = right - ((right - axis[0])*2) + diff

        # flip the block boxes
        for origin, box in zip(self.block_box_org, self.block_box):
            right = origin[0] + box.width
            if origin[0] < axis[0]:
                origin[0] = right + ((axis[0] - right)*2) + diff
            else:
                origin[0] = right - ((right - axis[0])*2) + diff

        # flip the axis
        axis[0] = width - self.axis[0]
        self.axis = tuple(axis)

        # reverse move_avatar
        mv = list(self.move_avatar)
        if mv[0] > 0:
            mv[0] = 0 - mv[0]
        else:
            mv[0] = abs(mv[0])
        self.move_avatar = tuple(mv)

    # update the hit boxes and rect position (from the parent and axis)
    def update(self, axis):
        x, y = self.adjust_position(axis)
        self.rect.topleft = (x, y)

        # update hit_boxes and dmg_boxes
        for hb1, hb2 in zip(self.dmg_box_org, self.dmg_box):
            hb2.topleft = (x + hb1[0], y + hb1[1])

        for hb1, hb2 in zip(self.hit_box_org, self.hit_box):
            hb2.topleft = (x + hb1[0], y + hb1[1])

        for hb1, hb2 in zip(self.block_box_org, self.block_box):
            hb2.topleft = (x + hb1[0], y + hb1[1])

    def load_image(self, filename):
        self.image, self.rect = gfx.load_image(filename)

    def load_sound(self, filename, sound_type=SOUND_PLAY):
        this_sound = sound.load_sound(filename)

        if   sound_type == SOUND_BLOCK:
            self.sound_block = this_sound

        elif sound_type == SOUND_HIT:
            self.sound_hit = this_sound

        elif sound_type == SOUND_MISS:
            self.sound_miss = this_sound

        else:
            self.sound = this_sound

    def __str__(self):
        return "FighterFrame \"%s\": %s" % (self.name, self.image)

# TODO: make this more like a list object.  slices, etc.
class Animation(object):
    """
    A container for a animation frames.

    To [hopefully] control memory use and loading times, animations are meant to be shared by
    other fighters in the game.  Each user of an animation is expected to know when to advance
    the frame and flip the images if needed.
    """

    def __init__(self, name=None):
        self.parent = None
        self.name = name
        self.frames = []
        self.modifier = 0       # modify the playback speed (not implemented)
        self.looping = 0        # if > 0, then loop x times.  -1 = forever
        self.loop_frame = 0     # if looping, then where to start again
        self.hold_play = False  # play and loop while button is held
        self.hold_loop = False  # loop while button is held, play at least once
        self.direction = 0      # this is the value in radians which direction this animation faces
                                # this value is used by the avatar class to properly display
                                # animations which are direction dependent.

    def __del__(self):
        print "dying animation", id(self)

    def __len__(self):
        return len(self.frames)

    def cleanup(self):
        [ frame.cleanup() for frame in self.frames ]
        self.__dict__ = {}

    def add_frame(self, frame):
        frame.parent = self
        self.frames.append(frame)

    def set_frame(self, no, frame):
        self.frames[no] = frame

    def __repr__(self):
        return "<Animation %s: \"%s\">" % (id(self), self.name)
