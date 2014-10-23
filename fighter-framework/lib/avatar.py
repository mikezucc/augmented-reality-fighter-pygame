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

import sys, weakref, pygame
from pygame.rect import Rect

import gfx, sound, engine
from animation import Animation, AnimationFrame
from engine import DrawableObject, Timer

# avatars are like sprites, but support multiple animations, collision detection
# an attached FSA will help control animations when controlled by player

# NOTE: sprites that finish and die need to be handled gracefully. if the death
# occurs while the sprite is being updated it messes up pygame,
# creates strange bugs, and makes me unhappy.


# btw, i named these things avatars before that stupid movie.

LEFT  = 0
RIGHT = 1

DEBUG = False
#DEBUG = True

DRAW_COLLISION_BOXES = 0

def debug(text):
    if DEBUG: sys.stdout.write(text)


# avatars can be compatable with pygame's dirtysprites
class PyGameDirtySpriteMixIn(object):
    #@property
    def get_rect(self):
        return self.current_frame.rect
        #return Rect(self.position, self.current_frame.rect.size)

    #@rect.setter
    def set_rect(self, rect):
        self.position = rect.topleft
        self.current_frame.rect = rect

    rect = property(get_rect, set_rect)

    #@property
    def get_image(self):
        return self.current_frame.image

    # if you set the image of an avatar, 
    # it changes the image for the current frame
    #@image.setter
    def set_image(self, image):
        cf = self.current_frame
        cf.image = image
        new_rect = image.get_rect()
        if cf.rect != None:
            old_pos = cf.rect.topleft
            new_rect.topleft = old_pos
            cf.rect = new_rect
        else:
            cf.rect = new_rect

    image = property(get_image, set_image)

    #@property
    def get_visible(self):
        return self._is_visible

    #@visible.setter
    def set_visible(self, value):
        self._is_visible = value

    visible = property(get_visible, set_visible)

# like a dirty sprite...
# dies when the frame is done playing
class StaticAvatar(DrawableObject, PyGameDirtySpriteMixIn):
    def __init__(self, parent=None):
        super(StaticAvatar, self).__init__()
        self.current_frame = AnimationFrame()
        self.facing = LEFT
        self.time = 0

    def __del__(self):
        print "dying avatar", id(self)

    def cleanup(self):
        self.current_frame.cleanup()
        self.__dict__ = {}

    def play(self, *arg, **kwarg):
        self.show()

    def update(self, time):
        self.time += time

    def get_time(self):
        return self.time

    def draw(self, surface):
        try:
            dirty_rect = surface.blit(self.current_frame.image, self.rect)
        except AttributeError:
            return None

        if DRAW_COLLISION_BOXES:
            try:
                flag      = pygame.BLEND_ADD
                dmg_box   = self.current_frame.dmg_box
                hit_box   = self.current_frame.hit_box
                block_box = self.current_frame.block_box
                #draw_rect = pygame.draw.rect
                for box in dmg_box:
                    s = pygame.Surface((box.width, box.height))
                    s.fill([150,25,25])
                    surface.blit(s, box, special_flags=flag)

                for box in hit_box:
                    s = pygame.Surface((box.width, box.height))
                    s.fill([0,150,50])
                    surface.blit(s, box, special_flags=flag)

                for box in block_box:
                    s = pygame.Surface((box.width, box.height))
                    s.fill([25,25,150])
                    surface.blit(s, box, special_flags=flag)

                dirty_rect.unionall_ip(dmg_box)
                dirty_rect.unionall_ip(hit_box)
            except AttributeError:
                pass

        return dirty_rect

    @property
    def state(self):
        return (self.current_animation, 0)

# simplified class for avatars with one animation
class SimpleAvatar(StaticAvatar):
    def __init__(self, parent=None):
        super(SimpleAvatar, self).__init__(parent)
        self.callback = None           # this is called when animation is finished
        self.current_frame_no = 0
        self.current_animation = None
        self.previous_frame = None
        self.callback = None
        self._is_paused = False
        self.looped = 0

        # timer initialization
        self.timer = Timer()

    # this is an override
    @property
    def state(self):
        return (self.current_animation, self.current_frame_no)

    def add_animation(self, anim):
        self.current_animation = anim

    """ BUG: we only test the next frame.  its possible the if the
    system is too slow that the animation could lag behind because
    frames won't get dropped """

    def update(self, time):
        self.time += time

        if self._is_paused == True: return

        # ttl == -1: special way to end an animation.
        if self.current_frame.ttl == -1:
            self.paused = True

        self.timer.update(time)

        if self.timer.finished:
            self.advance_frame()

    # sets the children of this to None, so that they can be garbage collected.
    # always call super last
    def cleanup(self):
        self.current_animation.cleanup()
        super(SimpleAvatar, self).cleanup()

    def advance_frame(self):

        if self._is_paused and self.current_frame.pause:
            return self.paused

        self.current_frame_no += 1

        if self.current_frame_no >= len(self.current_animation):
            # the animation has reached the end
            if self.current_animation.looping == 0:
                return self.stop()

            # loop, but count the loops
            elif self.current_animation.looping > 0:
                if self.looped > self.current_animation.looping:
                    self.stop()
                else:
                    self.set_frame(self.current_animation.loop_frame)
                    self.looped += 1

            # loop forever, don't count the loops
            else:
                self.set_frame(self.current_animation.loop_frame)
        else:
            # just set the next frame
            self.set_frame(self.current_frame_no)

    def set_frame(self, frame_no):
        # deref for speed
        new_frame = self.current_animation.frames[frame_no]

        self.previous_frame    = self.current_frame
        self.current_frame     = new_frame
        self.current_frame_no  = frame_no
        self.dirty = 1

        if new_frame.face(self.facing) == False:
            new_frame.update(self.position)

        # handle frames that may want to move the avatar's position
        pos = list(self.position)
        if new_frame.move_avatar != (0,0):
            pos[0] = pos[0] + new_frame.move_avatar[0]
            pos[1] = pos[1] + new_frame.move_avatar[1]

            # update the parent, engine will update us later
            self.parent.set_position(pos)
            new_frame.update(pos)

        new_frame.sound.stop()
        new_frame.sound.play()
        self.timer.alarm = self.current_frame.ttl 
        
    #@property
    def get_paused(self):
        return self._is_paused

    #@paused.setter
    def set_paused(self, value):
        self._is_paused = value
        if value == False:
            self.previous_frame_no = self.current_frame_no
            self.dirty = 0

    paused = property(get_paused, set_paused)

    def play(self, name=None, start_frame=0, callback=None, arg=[]):
        if self.paused:
            return

        # reset some state stuff
        self.looped = 0
        self.dirty  = 1
        self.paused = False

        if callback != None:
            self.callback = (callback, arg)

        debug("playing %s, %s: %s\n" % (self.current_animation, self.dirty, self))

        self.set_frame(start_frame)

    def stop(self):
        self.paused = True
        if self.callback != None:
            self.callback[0](*self.callback[1])

# avatar = animated sprite that can play multiple animations
class Avatar(SimpleAvatar):
    def __init__(self, parent):
        super(Avatar, self).__init__(parent)
        self.default = None         # what animation to play if not specified
        self.animations = {}            # the animations we can play
        self.loop_override       = False  # toggle force current animation loop
        self.loop_override_frame = None   # frame to loop if override applied

    # sets the children of this to None, so that they can be garbage collected.
    def cleanup(self):
        super(Avatar, self).cleanup()
        [ ani.cleanup() for ani in self.animations.values() ]

    # NOTE: if being reset, don't call the callback (animation didn't finish)
    def reset(self):
        """
        the FSA attached may be locked sometimes during a reset.
        in that case, the play default will fail, since it won't play
        animations when locked.  so, we need to unlock it, then relock
        the fsa if needed.
        """

        unlock = False

        try:
            if self.fsa.locked:
                unlock = True
        except:
            pass

        if self.default == None:
            print "No default animation set!", self
            self.current_animation = None
            self.current_frame_no = 0
            self.current_frame = None
            self.previous_frame = None
        else:
            if unlock:
                self.fsa.unlock()

            self.play(self.default)

            if unlock:
                self.fsa.lock()

    def face(self, d):
        self.facing = d

    def flip(self):
        self.facing = (self.facing + 1) % 2
        self.current_frame.face(self.facing)
        self.dirty = 1

    def set_frame(self, frame_no):
        # deref for speed
        new_frame = self.current_animation.frames[frame_no]

        self.previous_frame    = self.current_frame
        self.current_frame     = new_frame
        self.current_frame_no  = frame_no
        self.dirty = 1

        if new_frame.face(self.facing) == False:
            new_frame.update(self.position)

        # handle frames that may want to move the avatar's position
        try:
            pos = list(self.parent.position)
        except TypeError:
            print "bug: parent of", self, "not positioned properly (or at all)."
            raise
        if new_frame.move_avatar != (0,0):
            pos[0] = pos[0] + new_frame.move_avatar[0]
            pos[1] = pos[1] + new_frame.move_avatar[1]

            # update the parent, engine will update us later
            self.parent.set_position(pos)
            new_frame.update(pos)

        new_frame.sound.stop()
        new_frame.sound.play()
        self.timer.alarm = self.current_frame.ttl

    def play(self, name=None, start_frame=0, callback=None, arg=[]):
        print self, name
        # reset some state stuff
        self.looped = 0
        self.dirty = 1
        self.loop_override = False
        self.loop_override_frame = 0
        self.paused = False

        if callback != None:
            self.callback = (callback, arg)

        if name == None:
            name = self.default

        if isinstance(name, Animation):
            self.current_animation = name
        else:
            self.current_animation = self.get_animation(name)

        debug("playing %s, %s: %s\n" % (self.current_animation, self.dirty, self))

        self.set_frame(start_frame)

    def force_loop(self, loop=None, frame_no=0):
        if loop != None: self.loop_override = loop
        self.loop_override_frame = frame_no
        return self.loop_override

    def add_animation(self, anim):
        # set the animations parent to us (me?)
        anim.parent = self

        # make the first animation we add our default
        if self.animations == {}:
            self.animations[anim.name] = anim
            self.set_default(anim)
        else:
            self.animations[anim.name] = anim

    # return an animation by it's name.
    def get_animation(self, name):
        try:
            return self.animations[name]
        except KeyError:
            raise

    def set_default(self, name):
        if isinstance(name, Animation):
            self.default = name
            return
        else:
            try:
                self.default = self.animations[name]
            except KeyError:
                return

    def __str__(self):
        return "<Avatar %s>" % id(self)

# avatar with multiple animations
class MultipleAnimationAvatar(Avatar):
    def __init__(self):
        super(Avatar, self).__init__()

# avatar with special collision detection and handling
class FighterAvatar(Avatar):
    def __init__(self, parent):
        self.parent = parent
        self.previously_held = False # used to managle loop overrides
        self.fsa = None              # used to determine valid states
        super(FighterAvatar, self).__init__(parent)

    # this avatar deligate position to the parent for some reason
    #@property
    def get_position(self):
        return self.parent.position

    #@position.setter
    def set_position(self, position):
        self.parent.position = position

    position = property(get_position, set_position)

    def cleanup(self):
        super(FighterAvatar, self).cleanup()
        self.fsa = None

    def stop(self):
        super(FighterAvatar, self).stop()
        # reset causes the default animation to play, which should be
        # "idle".  if not, then it would make the fight act strangely
        self.reset()

    def update(self, time):
        self.timer.update(time)

        # deref for speed
        current_frame = self.current_frame

        if self.fsa != None:
            # mainly for recorded characters
            self.fsa.update(time)

            # check the fsa for held buttons
            # the fsa can veto the advance if the player is holding down a key
            if self.fsa.check_hold(self.state) == True:
                print "hold", self.state
                self.previously_held = True
                if current_frame.hold == True:
                    # continue updates, but don't redraw us
                    self.previous_frame = current_frame
                    self.dirty = 0
                    return

                if self.current_animation.hold_loop == True:
                    self.force_loop(True)

            # button is not being held
            else:
                if self.current_animation.hold_play == True:
                    self.stop()
                    return

                if self.previously_held == True:
                    print "unhold."
                    # we are not holding the key down [anymore]. unset loop override
                    self.force_loop(False)
                    self.previously_held = False

        if self.current_frame.ttl == -1:
            self.paused = True

        if self.timer.finished:
            self.advance_frame()

    # attack stuff =====================================================
    def negotiate_attack(self, attack):
        # this is the GameObject connected the the other avatar in the
        # collision.
        other = attack[1].parent.parent.parent.parent

        # doesn't seem to help
        #gfx.group.move_to_front(self)

        # hit valididity is decided by other fighter
        result = other.handle_attack(attack)

        # hit is valid
        if result == True:
            self.attack_landed(attack)

        # hit was blocked
        if result == False:
            self.attack_blocked(attack)

        # hit is not valid
        if result == None:
            self.attack_missed()

    # an attack we made hit something else
    def attack_landed(self, attack):
        print "hit!!!"

        self.current_frame.sound_hit.stop()
        self.current_frame.sound_hit.play()
        
        attack[1].parent.parent.parent.parent.been_hit(attack)

        if self.current_frame.hit_spawn != None:
            hc = self.current_frame.hit_spawn()
            #print intersection, hc.position
            hc.position = attack[1].clip(attack[0]).center
            
            # we need to get the current world to create the hc
            w = self.parent.match.world
            w.add(hc)
            hc.play()
            #print hc.position

    # an attack we made missed the target
    def attack_missed(self, attack=None):
        self.parent.attack_missed(attack)

        self.current_frame.sound_miss.stop()
        self.current_frame.sound_miss.play()

    # an attack we made was blocked by something
    def attack_blocked(self, attack):
        #attack[1].parent.parent.parent.parent.attack_blocked(attack)

        # dont understand, but this calls blocked on other fighter
        self.parent.attack_blocked(attack)
        if self.current_frame.sound_block == sound.dummy:
            self.current_frame.sound_miss.stop()
            self.current_frame.sound_miss.play()
        else:
            self.current_frame.sound_block.stop()
            self.current_frame.sound_block.play()

        if self.current_frame.block_spawn != None:
            hc = self.current_frame.block_spawn()
            hc.position = attack[1].clip(attack[0]).center
            w = self.parent.match.world
            w.add(hc)
            hc.play()

    # ==========================================================================

    def set_frame(self, frame_no):
        super(FighterAvatar, self).set_frame(frame_no)
        self.check_collision()

    def set_fsa(self, fsa):
        self.fsa = fsa

    def check_collision(self):
        # no use checking if this frame doesn't attack
        if self.current_frame.hit_box == []:
            return

        # this makes sure frames don't attack while avatar is paused
        if self.previous_frame == self.current_frame:
            return

        for a in self.resolve_attack(self.current_frame):
            self.negotiate_attack(a)
            return              # only handle one attack....for now
        
        # it was a miss
        self.attack_missed()

    # return any collisions
    def resolve_attack(self, frame):
        attacks   = []
        dmg_boxes = []

        # get all the avatars in the match
        other_avatars = [ f.avatar for f in self.parent.match.fighter ]
        
        # remove the attacking avatar
        other_avatars.remove(frame.parent.parent)

        # list of frames that could be attacked
        other_frames = [ a.current_frame for a in other_avatars \
            if hasattr(a.current_frame, "dmg_box")]

        # needed?
        #[ f.update() for f in other_frames ]

        [dmg_boxes.extend(f.dmg_box) for f in other_frames]

        # make a list of attack pairs (attacking frame, hit frame)
        for hit_box in frame.hit_box:
            [ attacks.append((hit_box, dmg_boxes[c])) for c in hit_box.collidelistall(dmg_boxes) ]

        return attacks

    def advance_frame(self):
        # just pause
        if self._is_paused and self.current_frame.pause:
            return self.paused

        self.current_frame_no += 1

        # the animation has reached the end
        if self.current_frame_no >= len(self.current_animation):
            print "loop?"

            # handle the loop override...why?  i don't remember...
            if self.loop_override == True:
                self.set_frame(self.current_animation.loop_frame)

            elif self.current_animation.looping == 0:
                print "no. 1"
                return self.stop()

            # loop, but count the loops
            elif self.current_animation.looping > 0:
                if self.looped > self.current_animation.looping:
                    print "no. 2"
                    self.stop()
                else:
                    print "loop."
                    self.set_frame(self.current_animation.loop_frame)
                    self.looped += 1

            # loop forever, don't count the loops
            else:
                print "loop."
                self.set_frame(self.current_animation.loop_frame)
        else:
            # just set the next frame
            self.set_frame(self.current_frame_no)

    #def play(self, animation=None):
    #   if self.fsa.locked:
    #       return
    #
    #   super(FighterAvatar, self).play(animation)
    #   # override looping if we are using hold-loop
    #   self.loop_override = self.current_animation.hold_loop

    def play(self, *arg, **kwarg):
        try:
            if self.fsa.locked:
                return
        except AttributeError:      # might not have a fsa [yet]
            pass

        super(FighterAvatar, self).play(*arg, **kwarg)

        # for combos
        if self.fsa != None:
            self.fsa.set_anim(self.current_animation)

        # handle auto-facing
        #if self.current_animation.name[:4] == "walk":
            #pos = self.parent.position
            #foe = self.parent.parent.closest_foe(self.parent)
            #if pos[0] < foe.position[0]:
                #if self.facing != 1:
                    #self.face(1)
            #elif pos[0] > foe.position[0]:
                #if self.facing != 0:
                    #self.face(0)
