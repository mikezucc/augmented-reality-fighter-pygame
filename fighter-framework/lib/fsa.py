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

"""
modified state machine.  controls player input

output an animation if input is valid

usage:
    add states and transitions

when input is recv'd, call process with the input

check the avatar's state
determin if we can continue
return animation if ok, else return False

internal state should generally match the avatar.

lazy internal state.  ie: don't really spend too much trying to keep in sync
w/avatar.  just check it as needed.

state = (animation object, current frame)
"""

import sys

DEBUG = True

def debug(text):
    if DEBUG: sys.stdout.write(text)



STICKY = 1
ANIMATION_CHANGE_TOKEN = 0
HOLD_TOKEN = 1
UNHOLD_TOKEN = 2

from collections import deque
from pygame.locals import *

import cPickle as pickle

# only have one child, an avatar.
class FSA(object):
    """
    Somewhat like a finite state machine.

    Accepts input in the form of button press constants (see buttons.py for constants) and
    controls an avatar's animations based on them.

    FSA's can be programmed to handle button combos and animation combos.  If a specific
    sequence of buttons or animations is handled, then the FSA can play another animation.

    FSA's must be programmed before use by feeding it state transistions.  See ikguy.py for an
    example on how to program a FSA.
    """

    def __init__(self, avatar):
        self.avatar = avatar            # avatar we are attached to
        self.combos = {}                # combos are executed after certain animations are played
        self.button_combos = []         # button combos are based on input, not animation
        self.holds = {}                 # keep track of state changes from holds
        self.hold = 0                   # keep track of buttons held down
        self.state_transitions=deque()  # conditions for changing animations
        avatar.set_fsa(self)
        self.locked = False

        # for animation combos
        self.move_history = []

        # for button combos
        self.button_history = []

        self.time = 0

    def reset(self):
        self.locked = False
        self.holds = {}
        self.hold =  0
        self.move_history = []

    def lock(self):
        self.locked = True
        print self, "lock"
        
    def unlock(self):
        self.locked = False
        print self, "unlock"

    def check_hold(self, state):
        """ avatar wants to change the animation (usually just the frame,
        we have the option of overriding it here.
        return a animation if override is to be used used for recording
        move (animation) history as well.
        no real need to update every frame...yet

        more like a request than a statement... "please, can i change state"?

        return:
            False:   Not holding
            True:    Holding, don't change the state
        """

        anim, frame_no = state

        # DON'T CHANGE THIS!!! (!!!)
        if self.hold == 0:
            return False
        else:
            for cmd, a in self.holds.items():
                print "check:", self.hold, cmd, a, anim, self.hold & cmd
                if ((self.hold & cmd) == cmd) and (a == anim):          
                    debug("DENY state change req. %s %s\n" % (state, self.hold))
                    return True

            debug("OK state change req. %s %s\n" % (state, self.hold))
            return False

    def set_anim(self, anim):
        if anim.name == "idle":
            """ avatar wants to idle, but lets make sure player isn't holding
            down any keys first.
            """
            self.move_history = []
        else:
            self.move_history.append(anim)

    # sticky means the avartar should finish the previous animation
    # when new one finishes
    # used for stances, (crouch to sweep, block to punch, etc)
    def add_transition(self, cmd, state1, state2, frame2=0, frame1=-1, flags=0):
        """
        add new "transition".

        these are basically just new states with a condition
        """

        # store the tranistions as objects, not strings
        try:
            state1 = ( self.avatar.get_animation(state1), frame1 )
            state2 = ( self.avatar.get_animation(state2), frame2 )
        except KeyError:
            print "Error while setting up fighter."
            print "Animation does not exist."
            raise

        # index:  0      1       2       3
        t =      (cmd, state1, state2, flags)
        self.state_transitions.append(t)

    def add_button_combo(self, animation, timeout, *buttons):
        """
        add a new button combo.

        button combos are executed when a series of buttons are pressed quickly.
        timeout specifies a limit on the time allowed between each button press
        """

        combo = [self.avatar.get_animation(animation), timeout/1000.0]
        combo.extend(buttons)
        combo = tuple(combo)
        self.button_combos.append(combo)

    def add_combo(self, animation, *combo):
        """
        add a new combo.

        a combo is a list of animations.  if it matches the command history,
        then execute another animation.

        command history is cleared each time the fighter idles, so it is safe
        to assume that the command sequence starts from an idle
        """

        # bug: we should raise if a duplicate combo is attempted to be added

        # create a temp ref for speed
        getter = self.avatar.get_animation

        # make a list of animation objects for the list of names
        cooked = tuple([ getter(a) for a in combo ])

        # store it in our lookup hash thingy
        self.combos[cooked] = (getter(animation), 0)

    def set_default_transition(self, t):
        pass

    def get_transition(self, cmd, state):
        if self.locked:
            return False

        # return a state if possible
        #print "===================================================="
        for t in self.state_transitions:
            #print t
            t_frame = t[1][1]
            if (t[0] & cmd == cmd) and (t[1][0] == state[0]):
                if (t_frame == state[1]) or (t_frame == -1):
                    return t
        return False

    def process(self, cmd, pressed):

        print "keys:", cmd, self.hold, pressed

        if pressed:
            now = self.time

            # check for button combos
            t = []
            state = None
            for bh in self.button_history:
                print "hist:", now, bh[0][1], bh[2]
                if (bh[2] + bh[0][1] >= now) and (cmd == bh[0][bh[1]+1]):
                    if len(bh[0])-1 == bh[1]+1:
                        return (bh[0][0], 0)
                    else:
                        t.append((bh[0], bh[1]+1, now))
            
            self.button_history = t

            # check for new combos
            for bc in self.button_combos:
                print "combo:", cmd, bc, self.button_combos
                if bc[2] == cmd:
                    i = [ bh for bh in self.button_history if bh[0] == bc ]
                    if i == []:
                        bh = (bc, 2, now)
                        self.button_history.append(bh)

            self.hold += cmd

            if state == None:
                state = self.check_change(cmd, self.avatar.state)

                # this key caused a state change.  let's remember that
                if state != False:
                    self.holds[cmd] = state[0]

            return state

        else:
            state = self.avatar.state

            # sanity, i guess
            if self.hold & cmd == cmd:
                old_hold = self.hold
                self.hold -= cmd

                debug("KEYUP %s %s %s\n" % (cmd, self.hold, old_hold))

                # sometimes fails, not sure why
                try:
                    del self.holds[cmd]
                except KeyError:
                    pass

                # still holding a key
                if self.hold != 0:
                    print "holding..."
                    print self.hold, state
                    t = self.get_transition(self.hold, state)
                    if t != False:
                        debug("hold: %s\n" % self.hold)
                        if t[3] & STICKY == STICKY:
                            print "stick!", t[2]
                            return t[2]

        return False

    # see if this event will change our state, return animation if true
    def check_change(self, cmd, state):
        t = self.get_transition(cmd, state)
        if t == False:
            # the input isn't valid
            return False

        else:
            # input is valid, check if it makes a combo
            return self.get_combo(t[2])

    def get_combo(self, state):
        # return a combo if it exists, otherwise return the original state

        # we need a temp tuple to check if a combo has been entered
        # don't set move_history b/c the avatar will do it (self.set_state)
        temp = self.move_history[:]
        temp.append(state[0])

        #print "history: ", temp

        # check for a combo
        try:
            new_state = self.combos[tuple(temp)]
            self.move_history = []
            return new_state

        except KeyError:
            return state

    def update(self, time):
        self.time += time

class LoggingFSA(FSA):
    """
    FSA that records input and can play it back.

    Probably not working, as game has changed and this has not been tested.
    """

    def __init__(self, avatar):
        self.log = deque()
        self.timer = None
        self.record = False
        self.playing = False
        self.virtual_hold = False
        super(LoggingFSA, self).__init__(avatar)

    def check_hold(self, state):
        hold = super(LoggingFSA, self).check_hold(state)

        if self.record:
            if hold == True and self.virtual_hold == False:
                    self.virtual_hold = True
                    self.log.append((self.get_time(), HOLD_TOKEN))

            if hold == False and self.virtual_hold == True:
                    self.virtual_hold = False
                    self.log.append((self.get_time(), UNHOLD_TOKEN))

        if self.playing:
            return self.virtual_hold
        else:
            return hold

    def update(self, time):
        super(LoggingFSA, self).update(time)

        if self.playing:
            try:
                t = self.log[0][0]
            except:
                self.stop_playing()
                return

            if t <= self.get_time():
                f = self.log.popleft()
                self.handle_frame(f)

    def handle_frame(self, frame):
        # this will fail if there is a token in the que
        kind = frame[1]
        if kind == ANIMATION_CHANGE_TOKEN:
            self.avatar.play(*frame[2])

        elif kind == HOLD_TOKEN:
            self.virtual_hold = True

        elif kind == UNHOLD_TOKEN:
            self.virtual_hold = False

        #debug("frame: %s\n" % frame)

    def start_playing(self):
        debug("playing %s\n" % self.log)
        if len(self.log) > 0:
            self.stop_recording()
            self.playing = True
            self.reset_time()

    def stop_playing(self):
        self.playing = False

    def start_recording(self):
        self.log = deque()
        self.stop_playing()
        self.reset_time()
        self.record = True

    # not a true pause
    def pause_recording(self):
        self.record = False

    # not a true stop
    def stop_recording(self):
        self.record = False

    def get_time(self):
        return time() - self.timer

    def reset_time(self):
        self.timer = ms()

    # doesn't take into effect keyholds.
    def process(self, cmd, pressed):
        if self.playing == False:
            state = super(LoggingFSA, self).process(cmd, pressed)

            #if self.record and state != False:
            #   self.log.append((self.get_time(), ANIMATION_CHANGE_TOKEN, state))

            return state

        return False

    def save(self, filename=None):
        if filename == None:
            filename = "fighter1.sav"

        fh = open(filename, "w")

        pickle.dump(self.log, fh)

    def load(self, filename=None):
        if filename == None:
            filename = "fighter1.sav"

        fh = open(filename)

        self.log = pickle.load(fh)
