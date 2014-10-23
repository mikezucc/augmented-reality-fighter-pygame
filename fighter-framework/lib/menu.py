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
from cmenu import cMenu
from pygame.rect import Rect
from engine import StaticWorld
import match, gfx

import sys

class TitleMenu(GameState):
    def __init__(self, driver):
        self._driver = driver

        self.menu = cMenu(Rect((85,119),self._driver.get_size()),
            20, 5, 'vertical', 100,
            [('1 Player', self.single_game),
            ('2 Players', self.multi_game),
            ('Watch CPU', self.watch_game),
            ('Quit Game', self.quit_game)],
            font="fonts/lastninja.ttf", font_size=16)

        self.world = StaticWorld(self._driver.get_size())
        self.world.add(self.menu)

    def activate(self):
        super(TitleMenu, self).activate()
        self.menu.ready()
        self.reactivate()

    def reactivate(self):
        self._driver.get_screen().blit(gfx.load_image("images/bkgd-crop.png")[0], (0,0))
        pass

    def deactivate(self):
        pass

    def draw(self, surface):
        self.world.draw(surface)

    def key_event(self, key, unicode, pressed):
        self.menu.key_event(key, unicode, pressed)

    def update(self, time):
        self.menu.update(time)
        self.world.update(time)

    def single_game(self):
        new_match = match.create_match(self._driver, True, False)
        self._driver.start(new_match)

    def watch_game(self):
        new_match = match.create_match(self._driver, False, False)
        self._driver.start(new_match)

    def multi_game(self):
        new_match = match.create_match(self._driver, True, True)
        self._driver.start(new_match)

    def quit_game(self):
        sys.exit()
