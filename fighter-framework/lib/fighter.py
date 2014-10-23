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

from avatar import FighterAvatar
from engine import DrawableObject



class Fighter(DrawableObject):
    defeat_animations = []
    avatar_class = FighterAvatar

    @property
    def rect(self):
        return self.avatar.rect

    def __init__(self):
        super(Fighter, self).__init__()
        self.avatar = self.avatar_class(self)
        self.hp = 100
        self.controller = None
        self.auto_block = None
        self.time = 0

    # called when hp = 0, just falls, never to rise again...
    def defeat(self):
        if self.defeat_animations != []:
            self.avatar.play(self.defeat_animations[0])
            self.match.is_defeated(self)

    def draw(self, surface):
        return self.avatar.draw(surface)

    def update(self, time):
        self.avatar.update(time)
        self.time += time

    def set_position(self, position):
        self.position = position

    def reset(self):
        self.avatar.reset()

    def get_time(self):
        return self.time

    def setup(self):
        pass

    # some attack hit us
    def been_hit(self, attack):
        self.defeat()

    # really these should be handled by the attacking frame, not the
    # fighter.  fix sometime later.  =)

    # attack we made was blocked
    def attack_blocked(self, attack):
        pass
        
    # attack we made missed target
    def attack_missed(self, attack=None):
        pass
        
    # attack we made hit target
    def attack_landed(self, attack):
        pass

    # we are being attacked.
    # return True to take the hit.
    # return False to miss it
    # return None to block it
    def handle_attack(self, attack):
        return True

    def handle_command(self, cmd, pressed):
        pass

    def play_command(self, cmd, pressed):
        pass
