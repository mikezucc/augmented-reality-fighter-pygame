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

from states import GameState
from banner import Banner, TextBanner
from avatar import SimpleAvatar
from animation import Animation, AnimationFrame
import engine
import gfx

import pygame
import weakref
from pygame.locals import *
from time import time as ms

DEFAULT_CPU_DIFFICULTY = 60
CPU_VS_CPU_DIFFICULTY  = 85

# BUG: b/c of this there can only be one match at a time
global match_world
match_world = None

def create_match(driver, f1_human=True, f2_human=True):
    match = BasicMatch(driver)
    #match = TurnBasedMatch(driver, surface)
    return setup_match(match, f1_human, f2_human, reset=False)

# basically, a simple way to set up common match types
# used to change an existing match.
def setup_match(match, f1_human, f2_human, reset=True):
    import loader as fighter_loader
    from ikguy import IK_Guy
    from karateman import KarateMan
    from ai import AIBlocker, AIFighter
    from match import Match

    if reset:
        match.reset()

    if f1_human:
        fighter = fighter_loader.load_fighter("ik_guy", IK_Guy)
        #fighter = fighter_loader.load_fighter("karate_man", KarateMan)
    else:
        fighter = fighter_loader.load_fighter("simple_ik_guy", AIFighter)
        fighter.difficulty = DEFAULT_CPU_DIFFICULTY
        if f2_human == False:
            fighter.difficulty = CPU_VS_CPU_DIFFICULTY

    match.add_fighter(fighter)

    if f2_human:
        fighter = fighter_loader.load_fighter("ik_guy", IK_Guy, ([137,64,54], [255,255,255]))
    else:
        fighter = fighter_loader.load_fighter("simple_ik_guy", AIBlocker, ([137,64,54], [255,255,255]))
        fighter.difficulty = DEFAULT_CPU_DIFFICULTY
        if f1_human == False:
            fighter.difficulty = int(CPU_VS_CPU_DIFFICULTY * 1.5)

    match.add_fighter(fighter)

    return match

class MatchState(GameState):
    pass    

# abstract match.
class Match(GameState):
    def __init__(self, driver):
        self._driver  = driver
        self.reset()

    def reset(self):
        self.style = None           # 1v1, 2v1, 2v2, tag, etc
        self.rounds = 3
        self.fighter = []
        self.controller = []
        self.finished = False
        self.quit = False
        self.defeat = None
        self.current_round = 1
        self.next_match = (False, False)
        self.arena = None
        self.post_round_pause = False
        self.world = engine.StaticWorld(self._driver.get_size())
        self.world.view.set_background(gfx.load_image("images/bkgd-cropblack.png")[0])
        
    def update(self, time):
        self.world.update(time)

        if self.defeat != None:
            if self.defeat.avatar.current_frame.ttl == -1:
                if not self.post_round_pause:
                    self.post_round_pause = True
                    self.lock_player_input()
                    timer = engine.CallbackTimer(3000, self.next_round)
                    self.world.add(timer)

    def draw(self, surface):
        self.world.draw(surface)

    # ONLY to be used before we are going to be deleted
    def cleanup(self):
        [ f.cleanup() for f in self.fighter ]
        self.__dict__ = {}

    def activate(self):
        super(Match, self).activate()
        self.ready()

    def reactivate(self):
        pass
        
    def deactivate(self):
        pass

    def add_fighter(self, fighter):
        self.world.add(fighter)
        self.fighter.append(fighter)
        fighter.match = self

    def is_defeated(self, fighter):
        self.defeat = fighter

    def next_round(self):
        self.defeat = None
        self.post_round_pause = False

        self.current_round += 1
        if self.current_round > self.rounds:
            self._driver.done()
        else:
            self.ready()

    def finished(self):
        self._driver.done()

    def key_event(self, key, unicode, pressed):
        if not self.input_lock:
            [ c.play_key(key, pressed) for c in self.controller ]

    # prevent players (including cpu) from changing fighter's state
    def lock_player_input(self):
        [ f.fsa.lock() for f in self.fighter ]
        self.input_lock = True

    def unlock_player_input(self):
        [ f.fsa.unlock() for f in self.fighter ]
        self.input_lock = False

# match for 2 fighter on 1 dimensional plane
class BasicMatch(Match):
    def __init__(self, driver):
        super(BasicMatch, self).__init__(driver)
        self.background = gfx.load_image("images/bkgd-cropblack.png")[0]
        self.buff = gfx.load_image("images/bkgd-cropblack.png")[0]
        self.banner_image = \
            gfx.load_image_with_colorkey("images/fight_banner_border.png")

        self.input_lock = False

    def closest_foe(self, fighter):
        return self.fighter[abs(self.fighter.index(fighter)-1)]

    # add a Fighter class object to the match, not a file
    def add_fighter(self, fighter):
        super(BasicMatch, self).add_fighter(fighter)

        if len(self.fighter) == 1:
            self.controller.append(engine.MappedInput(fighter, engine.p1_key_def))
        else:
            self.controller.append(engine.MappedInput(fighter, engine.p2_key_def))

    def ready(self):
        # draw the background
        #gfx.set_background(self.background)

        # put fighters into position
        self.fighter[0].avatar.face(1)
        self.fighter[0].set_position((80, 194))

        self.fighter[1].avatar.face(0)
        self.fighter[1].set_position((240, 194))

        # make sure the default animation is played at start of fight
        [ f.reset() for f in self.fighter ]

        # an attempt to redraw the fighter
        [ setattr(f.avatar, "dirty", 1) for f in self.fighter ]

        self.lock_player_input()

        # uncomment to use the experimental "zoom feature"
        # not.
        #self.world.view.set_zoom_objects(self.fighter)

        # the banner must be played, since it unlocks the player input.
        # if you don't want to use the banner, then you should unlock
        # player input manually.
        self.banner = self.make_banner()
        self.banner.play()

    def make_banner(self):
        banner_x = 322 / 2 - (self.banner_image[1].width / 2)
        banner = SimpleAvatar()
        banner.position = (banner_x, 80)
        bf = AnimationFrame()
        bf.image, bf.rect = self.banner_image
        bf.ttl = 1500
        ani = Animation()
        ani.add_frame(bf)
        banner.add_animation(ani)
        self.world.add(banner)
        banner.callback = (self.close_banner, [])
        return banner
        
    def close_banner(self):
        self.unlock_player_input()
        self.banner.cleanup()       
        self.banner = None

    def key_event(self, key, unicode, pressed):
        super(BasicMatch, self).key_event(key, unicode, pressed)
        
        if not pressed:
            return

        if key == K_r:
            self.finished = True

        elif key == K_g:
            self.fighter[1].avatar.flip()

        elif key == K_f:
            self.fighter[0].avatar.flip()
            # HACK: clear up any buttons being held down.
            self.fighter[0].fsa.holds = {}
            self.fighter[0].fsa.hold = 0

        elif key == K_F1:
            match=create_match(self._driver, self._surface, False, False)
            self._driver.replace(match)

        elif key == K_F2:
            match=create_match(self._driver, self._surface, True, False)
            self._driver.replace(match)

        elif key == K_F3:
            match=create_match(self._driver, self._surface, True, False)
            self._driver.replace(match)

class TurnBasedMatch(BasicMatch):
    def pre_run(self):
        self.wait_timer = ms()
        self.fighter_input = [None, None]
        self.show_banner = True

    def ready(self):
        self.lock_player_input()

        self.fighter[0].avatar.face(1)
        self.fighter[0].set_position((150, 190))

        self.fighter[1].avatar.face(0)
        self.fighter[1].set_position((170, 190))

        # make sure the default animation is played at start of fight
        [ f.reset() for f in self.fighter ]

        banner_x = 322 / 2 - (self.fight_image.get_rect().width / 2)
        fight_banner = Banner(self.fight_image, (banner_x, 100), 1000)
        fight_banner.avatar.callback = (self.release_input_lock, [])
        fight_banner.show()

        self.pre_run()

    def update(self, time):
        for f in self.fighter:
            f.update(time)

        events = pygame.event.get([KEYUP, KEYDOWN, pygame.QUIT])
        self.get_system_input(events)
        self.get_player_input(events)
        #[ [ c.play_key(e) for c in self.controller ] for e in events ]

        # take input
        if self.wait_timer + 2 <= ms():
            for x in range(0, len(self.fighter)):
                event = self.fighter_input[x]
                if event != None:
                    self.controller[x].play_key(event)

                    # basically, allow the fighter to gracefully return to
                    # the last thing he/she was doing
                    if event.type == KEYDOWN:
                        new_event = pygame.event.Event(KEYUP, key=event.key)
                        self.fighter_input[x] = new_event
                    else:
                        self.fighter_input[x] = None


            self.show_banner = True
            self.wait_timer = ms()

        else:
            if self.show_banner == True:
                self.show_banner = False
                #msg = TextBanner("input now!", (100, 120), 1000)
                #msg.show()

            for event in events:
                for x in range(0, len(self.fighter)):
                    state = self.controller[x].handle_key(event)
                    if state != False:
                        self.fighter_input[x] = event
                        x_position = self.fighter[x].position[0]
                        #msg = TextBanner(state[0].name, (x_position, 192), 2000)
                        #msg.show()
