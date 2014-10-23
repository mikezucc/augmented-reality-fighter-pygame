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

import fighter
import random

class AutoBlocker(fighter.Fighter):
    block_cooldown = 240                # milliseconds cooldown
    banned_animations = ["forward flip", "backward flip"]

    def cleanup(self):
        #world.remove(self.timer)
        #self.timer = None
        pass

    def setup(self):
        super(AutoBlocker, self).setup()
        self.block_frames = []

        temp = []
        [ temp.append(self.avatar.get_animation(ani)) for ani in AutoBlocker.banned_animations ]
        self.banned_animations = temp

        # make a list of frames that could block an attack
        for anim in self.avatar.animations.values():
            if anim not in self.defeat_animations:
                if anim not in self.banned_animations:
                    if anim.frames[0] != []:
                        self.block_frames.append(anim.frames[0])

        # sub the cool down so a block can happen right away
        self.last_block = self.get_time() - self.block_cooldown
        
        """self.timer = CallbackTimer(
        self.block_cooldown, self.unlock_auto_block)
        world.add(timer)
        """

    def handle_attack(self, attack):
        if self.will_block():
            blocks = self.plan_block(attack)
            if blocks != []:
                self.set_auto_block(attack)
                self.avatar.play(blocks[0])
                self.avatar.paused = True
                if attack[0].collidelist(blocks[0].frames[0].block_box) > -1:
                    # block
                    return False
                else:
                    # evade
                    return None
        else:
            return True

    def will_block(self):
        """
        just a simple way of determining whether to auto-block or not
        """

        return True

        if self.last_block + self.block_cooldown <= self.get_time():
            if random.randint(0, 100) == 0:
                return True

        return False

    def unlock_auto_block(self):
        self.auto_block = None

    # autoblock: should constantly test if blocking will prevent the hit.
    # otherwise,it causes strange blocks, like a medium kick to a fist
    # block, but still "hits"
    def set_auto_block(self, attack):
        self.last_block = self.get_time()
        self.auto_block = (attack[0], attack[1])

    def update(self, time):
        self.avatar.update(time)

        if self.auto_block != None:
            # test if the attack's frame is still the same as when attacked
            avatar = self.auto_block[0].parent.parent.parent

            if avatar.current_frame != self.auto_block[0].parent:
                self.avatar.reset()
                self.auto_block = None

    # moves that could cause a block (parry)
    def plan_block(self, attack):
        hit   = attack[0]
        other = attack[0].parent.parent.parent

        # we have to call update() on the frames to update hitboxes 
        [ frame.face(self.avatar.facing) for frame in self.block_frames ]
        [ frame.update(self.position) for frame in self.block_frames ]

        return [ frame.parent for frame in self.block_frames \
            if hit.collidelistall(frame.block_box) != [] ]

    def update_block_frames(self):
        # we have to call update() on the frames to update hitboxes 
        [ frame.face(self.avatar.facing) for frame in self.block_frames ]
        [ frame.update(self.position) for frame in self.block_frames ]
