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

from fighter import Fighter
from engine import Timer, CallbackTimer
from fsa import FSA
import gfx
import random


class AIFSA(FSA):
    def check_hold(self, state):
        # hackish thing to simulate holding down a key
        if self.avatar.current_animation.hold_play:
            return True
        else:
            return False

class CpuFighter(Fighter):
    """
    Base class for CPU opponents.
    Includes some common AI elements and an fsa to control animations
    """

    def setup(self):
        self.fsa = AIFSA(self.avatar)
        super(CpuFighter, self).setup()

    def reset(self):
        self.fsa.unlock()
        super(CpuFighter, self).reset()

    # an attack that we made has been blocked
    def attack_blocked(self, attack):
        super(CpuFighter, self).attack_blocked(attack)
        self.stun(300)

    def stun(self, time):
        self.avatar.paused = True
        self.fsa.lock()
        timer = CallbackTimer(time, self.recover_stun)
        self.match.world.add(timer)
        
    def recover_stun(self):
        self.avatar.paused = False
        self.fsa.unlock()

class AIBlocker(CpuFighter):
    """
    CPU AI class that will block attacks.
    Can be used as a base class for human players to provide autoblocking

    The trick used here is unique because of the animation ripped from IK+.
    Most animations are only 2-3 frames long, and the 1st or 2nd frame in
    some animations could be used as a block.  The autoblock works by first
    detecting a hit from the other fighter, then changing the animation to
    on that includes a blocking frame, which could be a kick, block, etc.

    It is cheating, in a pure sense, since it relies on first taking a hit.
    Other solutions may come later.
    """

    forward_animation   = "walk forward"
    backward_animation  = "walk backward"
    idle_animation      = "idle"
    defeat_animations   = ["fall backward", "fall forward"]
    banned_animations   = ["crazy"]

    difficulty     = 10     # x/100
    update_freq    = 30     # milliseconds between updating
    personal_space = 50     # will not move if distance is less than x
    aggressiveness = 100    # x/100


    def reset(self):
        super(AIBlocker, self).reset()

    def setup(self):
        super(AIBlocker, self).setup()

        # change milliseconds to seconds (as returned by the system clock)
        self.movement_timer = Timer()
        self.movement_timer.alarm = self.update_freq

        self.block_timer = Timer()

        temp = []   
        for ani in AIBlocker.defeat_animations:
            try:
                temp.append(self.avatar.get_animation(ani))
            except KeyError:
                pass
        self.defeat_animations  = temp

        get_animation = self.avatar.get_animation
        self.forward_animation  = get_animation(self.forward_animation)
        self.backward_animation = get_animation(self.backward_animation)
        self.idle_animation     = get_animation(self.idle_animation)

        # block frames are frames that contain hitboxes that can block attacks
        self.block_frames = []

        # search all the animations and make a list of block frames
        for anim in self.avatar.animations.values():
            if anim not in self.defeat_animations:
                if anim.frames[0] != []:
                    self.block_frames.append(anim.frames[0])

    # make sure fighter has enough space to fight, and is not
    # moving out-of-bounds.  return True if avatar needs to change
    def position_self(self):
        foe = self.match.closest_foe(self)
        x = self.position[0]

        if self.avatar.facing == 0:
            if foe.position[0] > x:
                self.reset()
                self.avatar.face(1)
                return True
        else:
            if foe.position[0] < x:
                self.reset()
                self.avatar.face(0)
                return True

        #if self.avatar.current_animation != self.idle_animation:
        #   return False

        # left bounds of screen
        if x < 40:
            self.avatar.face(1)
            self.avatar.play(self.forward_animation)
            return True

        # right bounds
        elif x > 290:
            self.avatar.face(0)
            self.avatar.play(self.forward_animation)
            return True

        return False

    # used to back away from the other fighter
    def get_space(self):
        foe = self.match.closest_foe(self)
        x = self.position[0]

        if self.avatar.current_animation != self.idle_animation:
            return False

        if abs(x - foe.position[0]) <= self.personal_space:
            if random.random() <= .75:
                self.avatar.play(self.backward_animation)
            else:
                self.avatar.play(self.forward_animation)
            return True

        # stop walking!
        elif self.avatar.current_animation in \
            [self.backward_animation, self.forward_animation]:
            self.reset()
            return True

    # rising means that odds are higher as difficulty is higher
    def rand_diff(self, easy, difficult):
        if easy > difficult:
            mod = float(float(100-self.difficulty) / float(100))
            magic = int(mod * float(easy - difficult) + difficult)
        else:
            mod = float(float(self.difficulty) / float(100))
            magic = int(mod * float(difficult - easy) + easy)

        #print "Magic:", magic

        if random.randint(0, magic) == 0:
            return True
        else:
            return False

    def update(self, time):
        self.avatar.update(time)
        self.movement_timer.update(time)

        # dead, dont do anything
        if self.avatar.current_animation in self.defeat_animations:
            return True     

        if self.movement_timer.finished:
            # make sure we are in the area
            if self.position_self():
                self.movement_timer.alarm = random.randint(300, 700) 
                return True

            # position ourselves away from the opponent
            if self.get_space():
                self.movement_timer.alarm = random.randint(300, 800) 
                return True

            #elif self.avatar.current_animation in \
            #   [self.backward_animation, self.forward_animation]:
            #   self.reset()
            #   return True

            self.movement_timer.alarm = self.update_freq * 4

        if self.auto_block != None:
            self.block_timer.update(time)

            if self.block_timer.finished:
                self.unset_hold()
                return True

            # test if the attack's frame is still the same as when attacked
            avatar = self.auto_block[1].parent.parent.parent

            # stop blocking when the other player's animation frame changes
            if avatar.current_frame != self.auto_block[1].parent:
                #self.unset_hold()
                pass

    def handle_attack(self, attack):
        if random.random() * 100 > 101 - self.difficulty:
            self.update_block_frames()

            other = attack[0].parent.parent.parent
            block = self.plan_block(attack)

            # see if we can block
            if len(block) > 0:
                evasive_manuever = block[random.randint(0, len(block)-1)]
                self.avatar.play(evasive_manuever)
                return self._test_attack(attack)

            evade = self.plan_evade(attack)

            # nope, can we evade it?
            if len(evade) > 0:
                evasive_manuever = evade[random.randint(0, len(evade)-1)]
                self.avatar.play(evasive_manuever)
                r = attack[0].collidelist(self.avatar.current_frame.block_box)
                return self._test_attack(attack)

        else:
            return True

    def _test_attack(self, attack):
        r = attack[0].collidelist(self.avatar.current_frame.block_box)
        if r > -1:
            self.set_hold(attack)
            return False
        r = attack[0].collidelist(self.avatar.current_frame.dmg_box)
        if r > -1 : return True
        return None

    # moves that could cause a block (parry)
    def plan_block(self, attack):
        hit   = attack[0]
        other = attack[0].parent.parent.parent

        possible = [ frame.parent for frame in self.block_frames \
            if hit.collidelistall(frame.block_box) != [] ]

        return possible

    def plan_evade(self, attack):
        hit   = attack[0]
        other = attack[0].parent.parent.parent

        possible = [ frame.parent for frame in self.block_frames \
            if hit.collidelistall(frame.dmg_box) == [] ]

        return possible

    def update_block_frames(self):
        # we have to call update() on the frames to update hitboxes 
        [ frame.face(self.avatar.facing) for frame in self.block_frames ]
        [ frame.update(self.position) for frame in self.block_frames ]
        
    def set_hold(self, attack):
        self.auto_block = attack
        self.avatar.paused = True
        self.block_timer.alarm = 250 

    def unset_hold(self):
        self.auto_block = None
        self.avatar.paused = False


class AIFighter(AIBlocker):
    """
    CPU AI class that can perform attacks.

    Since this class cannot block, it should (and is) be a subclass of another
    class that can block.

    The built-in timer will determine when the AI will search for a move.  When
    the timer is finished, the class will search through attacking frames and
    determine which animations would deal damage, then choose one at random.
    """
 
    def setup(self):
        super(AIFighter, self).setup()
        self.all_frames     = []
        self.next_animation = None
        self.in_attack      = False         # flagged if we are attacking
        self.ai_timer = Timer()

        for anim in self.avatar.animations.values():
            if anim not in self.defeat_animations:
                self.all_frames.extend(anim.frames)

    def reset(self):
        super(AIFighter, self).reset()
        self.ai_timer.alarm = self.update_freq
        self.in_attack   = False

    def attack_landed(self, attack):
        super(AIFighter, self).attack_landed(attack)
        self.in_attack = False

    def attack_blocked(self, attack):
        super(AIFighter, self).attack_blocked(attack)
        self.in_attack = False

    def attack_missed(self, attack=None):
        super(AIFighter, self).attack_missed(attack)
        self.in_attack = False

    def handle_attack(self, attack):
        if self.in_attack:
            return True
        else:
            return super(AIFighter, self).handle_attack(attack)

    def set_hold(self, attack):
        # don't block during an attack
        super(AIFighter, self).set_hold(attack)
        hold = self.avatar.current_frame.ttl
        self.ai_timer.alarm = random.randint(hold, hold*3)

    def update(self, time):
        update = super(AIFighter, self).update(time)
        self.ai_timer.update(time)

        # the super has already made a change to the avatar
        if update == True:
            return True

        # we are attacking right now, so just let it be...
        if self.ai_timer.finished:
            # if we are attacking, then let it finish
            if self.in_attack:
                return

            # make it dumb by stopping once in a while
            if self.rand_diff(5, 40):
                self.ai_timer.alarm = random.randint(250, 1000) 
                return

            # get a list of stuff we could do here to punish
            options = self.plan_attack()

            # WE DON'T WANT THE BANNED ONES
            for ani in self.banned_animations:
                try:
                    options.remove(ani)
                except ValueError:
                    pass

            if options == []:
                # play random animation, just for variety
                if self.rand_diff(5, 15):
                    ani = self.block_frames[random.randint(0, len(self.block_frames)-1)].parent
                    self.avatar.play(ani)
                    self.ai_timer.alarm = random.randint(250, 1000)
                    return

                # if we are idling, then we can walk        
                foe = self.match.closest_foe(self)
                if self.avatar.current_animation == self.idle_animation:
                    if abs(foe.position[0] - self.position[0]) > self.personal_space:
                        self.avatar.play(self.forward_animation)
                        self.ai_timer.alarm = random.randint(60, 120) 
                        return True
    
            else:
                # throw an attack we can land
                if random.random() * 100 > 101 - self.difficulty:
                    if self.avatar.current_animation == self.idle_animation:
                        attack = options[random.randint(0, len(options)-1)]
                        self.avatar.play(attack)

                        # BUG: causes race conditions
                        #self.in_attack = attack
                        self.ai_timer.alarm = random.randint(200, 400) 
                        return
                    else:
                        self.avatar.play(self.idle_animation)
                        self.ai_timer.alarm = random.randint(120, 200) 

            self.ai_timer.alarm = self.update_freq

    # return a list of all frames that will land an attack 
    def plan_attack(self, state=None):
        [ frame.face(self.avatar.facing) for frame in self.all_frames ]
        [ frame.update(self.position) for frame in self.all_frames ]

        possible = [ frame.parent for frame in self.all_frames \
            if self.avatar.resolve_attack(frame) != [] ]

        return possible
