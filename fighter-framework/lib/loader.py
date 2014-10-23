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

import gfx, game
from animation import Animation, AnimationFrame, FighterFrame, CollisionBox
from avatar import Avatar, FighterAvatar, SimpleAvatar

from configobj import ConfigObj
import os, os.path, sys, re

from pygame import Rect
import pygame

from animation import SOUND_HIT, SOUND_BLOCK, SOUND_MISS, SOUND_PLAY


DEBUG = False

def debug(text):
    if DEBUG: sys.stdout.write(text)

fighters_root = os.path.join(game.resource_path, "fighters")
color_swap = None

def handle_bool(d, name, default=False):
    try:
        text = d[name].strip().lower()
    except KeyError:
        return default

    if text.lower() == "true":   return True
    if text.lower() == "yes":    return True
    if text.lower() == "no":     return False
    if text.lower() == "false":  return False
    raise ValueError

def load_fighter(name, class_name=None, colorize=None):
    global color_swap
    color_swap = colorize

    # this module is a huge kludge and does a bunch of stuff that i don't
    # really want to explain...  anyway, there is a hack here.
    old_path = game.resource_path
    game.resource_path = "."

    debug("loading fighter...\n")

    fighter = class_name()

    root            = os.path.join(fighters_root, name)
    animations_path = os.path.join(root, "animations")

    try:
        #TODO: add a test here
        pass
    except OSError:
        print "cannot find or access fighter folder: \"%s\"." %name
        print "please make sure the folder exists and is readable."
        raise

    load_animations(animations_path, fighter.avatar)

    # do stuff with the FSA...if any
    fighter.setup()
    fighter.avatar.set_default("idle")

    # end hack
    game.resource_path = old_path

    return fighter

def load_animations(path, avatar):
    debug("loading animations:\n")

    for name in os.listdir(path):
        if name[0] != ".":
            debug("  \"%s\"..." % name)
            filename  = os.path.join(path, name, "anim.def")
            animation = read_animation_def(filename, name, FighterFrame)
            avatar.add_animation(animation)
            debug("done\n")

def read_animation_def(filename, name, frame_klass=AnimationFrame):
    reader      = ConfigObj(filename)
    animation   = Animation(name)
    path        = os.path.split(filename)[0]
    range_regex = re.compile(".*?(\d*)\s*-\s*(\d*)")

    # stores information that affects all frames in the animation
    animation_dict = {}

    try:
        animation_dict.update(reader['general'])
    except KeyError:
        pass

    for section, values in reader.items():
        d = {}
        # update for the "globals"
        d.update(animation_dict)
        d.update(values)

        if section[:5].lower() == "frame":
            start = None
            end   = None

            try:
                # frames can define a range of frames
                start, end = range_regex.match(section).groups()
                start = int(start)
                end   = int(end)

            except AttributeError:
                pass

            # load a single frame
            if start == None:
                d['name'] = section[6:]
                frame = load_frame(path, d, frame_klass)
                animation.add_frame(frame)

            # load a range of frames
            else:
                prefix, suffix = get_frame_image_filename_prefix_suffix(d)
                for x in range(start, end + 1):
                    # mangle the dict to reflect the right image_file
                    d['file'] = prefix + str(x) + suffix
                    d['name'] = str(x)
                    frame     = load_frame(path, d, frame_klass)
                    animation.add_frame(frame)

        if section.lower() == "animation":

            # loop entire animation when held
            animation.hold_loop = handle_bool(d, 'hold loop')
            print animation, animation.hold_loop


            # play while held [stop when let go]
            animation.hold_play = handle_bool(d, 'hold play')
            print animation, animation.hold_play

    return animation

def get_masks_from_image(file_name):
    """
    attempt to load a mask file and get hit boxes from it.

    hitboxes in the image can touch, but cannot overlap.
    they must be rectangles with straight edges.
    a dict defining the colors to search for can be passed.

    """

    if os.access(file_name, os.F_OK) == False:
        return

    mask, rect = gfx.load_image(file_name, use_cache=False)
    pxarray = pygame.PixelArray(mask)

    width, height = rect.size
    height = height - 1

    # could be slow, but idk another way
    y = 0
    rects = []
    while y <= height:
        rect        = None
        last_color  = None
        for x in range(0, width):
            color = mask.unmap_rgb(pxarray[x][y])[:3]

            if last_color != color:
                if (rect == None) and (color != (0,0,0)):
                    rect = [x,y,None,None,color]
                elif rect != None:
                    existing = False
                    rect[2] = x - 1
                    for r in rects:
                        if r[3] == None:
                            if (r[0] == rect[0]) and (r[1] == rect[1] - 1) and (r[2] == rect[2]) and (r[4] == rect[4]):
                                r[3] = y
                                existing = True
                        elif (r[0] == rect[0]) and (r[3] == rect[1] - 1) and (r[2] == rect[2]) and (r[4] == rect[4]):
                            r[3] = y
                            existing = True

                    if existing == False:
                        #print r, rect, x, y
                        rects.append(rect)
                    if color != (0,0,0):
                        rect = [x,y,None,None,color]

            last_color = color
        y += 1
   
    if rect != None:
        rect[2] = x - 1
        for r in rects:
            if r[3] == None:
                if (r[0] == rect[0]) and (r[1] == rect[1] - 1) and (r[2] == rect[2]) and (r[4] == rect[4]):
                    r[3] = y
            elif (r[0] == rect[0]) and (r[3] == rect[1] - 1) and (r[2] == rect[2]) and (r[4] == rect[4]):
                r[3] = y

def get_frame_image_filename_prefix_suffix(d):
    try:
        suffix = d['file suffix']
    except KeyError:
        suffix = ""

    try:
        prefix = d['file prefix']
    except KeyError:
        print "cannot find prefix for frame."
        print "you may ned to review the def.  may need to specify the file"
        raise

    return prefix, suffix


def get_frame_image_filename(d):
    try:
        image_filename = d['file']
    except KeyError:
        # DONT PANIC
        prefix, suffix = get_frame_image_filename_prefix_suffix(d)
        image_filename = prefix + d['name']

    return image_filename

def load_frame(path, d, klass=AnimationFrame):
    global color_swap

    image_filename = get_frame_image_filename(d)
    image_file = os.path.join(path, image_filename)
    sound_path = os.path.normpath(os.path.join(path, "../../sounds"))

    frame = klass()
    frame.name = d['name']

    try:
        if d['transparency'] == 'colorkey':
            frame.image, frame.rect = gfx.load_image_with_colorkey(image_file)
        if d['transparency'] == 'pixel':
            frame.image, frame.rect = gfx.load_image_with_alpha(image_file)
    except KeyError:
        frame.image, frame.rect = gfx.load_image_with_alpha(image_file)

    name = d['file']
    mask_file = os.path.join(path, name[:name.index(".")] + "-mask" + name[name.index("."):])
    get_masks_from_image(mask_file)

    if color_swap != None:
        new_image = frame.image.copy()
        pxarray = pygame.PixelArray(new_image)
        pxarray.replace(color_swap[0], color_swap[1])
        new_image.unlock()

        # check if this is cached already:
        cached = gfx.get_image_from_cache(None, new_image)

        if cached != None:
            frame.image = cached
        else:
            gfx.add_image_to_cache(new_image)
            frame.image = new_image

    try:
        # change str's to int's
        frame.axis = (int(d['axis'][0]), int(d['axis'][1]))
    except ValueError:
        if d['axis'] == "center".lower():
            frame.axis = frame.rect.center
        else:
            print path
            print "ERROR: axis improperly formatted"
            raise

    except IndexError:
        print path
        print "ERROR: axis improperly formatted"
        raise

    frame.ttl = float(d['ttl'])

    if d.has_key('move'):
        frame.move_avatar = (int(d['move'][0]), int(d['move'][1]))

    try:
        for x in range(1,6):
            section_name = "dmg box" + str(x)
            if d.has_key(section_name):
                hb = [int(x) for x in d[section_name]]
                box = CollisionBox(hb[:2], (hb[2]-hb[0]+1, hb[3]-hb[1]+1))
                frame.add_dmg_box(box)

        if d.has_key('block box'):
            hb = [int(x) for x in d['block box']]
            box = CollisionBox(hb[:2], (hb[2]-hb[0], hb[3]-hb[1]))
            frame.add_block_box(box)

        if d.has_key('hit box'):
            hb = [int(x) for x in d['hit box']]
            box = CollisionBox(hb[:2], (hb[2]-hb[0], hb[3]-hb[1]))
            frame.add_hit_box(box)

    except ValueError:
        print ""
        print "ERROR: improperly formatted hitbox"
        raise ValueError

    if d.has_key('block sound'):
        filename = os.path.join(sound_path, d['block sound'])
        frame.load_sound(filename, SOUND_BLOCK)

    if d.has_key('hit sound'):
        filename = os.path.join(sound_path, d['hit sound'])
        frame.load_sound(filename, SOUND_HIT)

    if d.has_key('miss sound'):
        filename = os.path.join(sound_path, d['miss sound'])
        frame.load_sound(filename, SOUND_MISS)

    if d.has_key('sound'):
        filename = os.path.join(sound_path, d['sound'])
        frame.load_sound(filename, SOUND_PLAY)

    for section_name in ("block spawn", "hit spawn"):
        if d.has_key(section_name):
            name       = d[section_name]
            extra_path = os.path.normpath(os.path.join(path, "../../extra"))
            anim_path  = os.path.join(extra_path, name, "anim.def")
            anim       = read_animation_def(anim_path, name)
            frame.__dict__[section_name.replace(" ","_")] = make_factory(anim)

    # the good way
    frame.hold  = handle_bool(d, 'hold', False)
    frame.pause = handle_bool(d, 'pause', True)

    return frame

# possible problems with hitconfirms:
# references to frames may cause problems when multiple hit confirms are displayed
# slow b/c constructor has to do some stuff...metaclass maybe can resolve

class MetaHitConfirm(type):
    def __init__(cls, name, bases, d):
        # add the animation to the metaclass
        #d['animation'] = animation

        super(MetaHitConfirm, cls).__init__(name, bases, d)
        #print "META", cls, name, bases, d

# don't do a normal cleanup (protect the animation from being lost)
class HitConfirm(SimpleAvatar):
    __metaclass__ = MetaHitConfirm

    def __init__(self):
        super(HitConfirm, self).__init__()
        self.add_animation(self.animation)
        self.callback = (self.really_stop, [])

    def __del__(self):
        print "dying hc", id(self)

    # causes the rendere to remove us from updates
    def really_stop(self):
        self.current_frame = None
        self.current_animation.parent = None

# all instances share the same animation
def make_factory(anim):
    class HitConfirmed(HitConfirm):
        animation = anim

    return HitConfirmed

