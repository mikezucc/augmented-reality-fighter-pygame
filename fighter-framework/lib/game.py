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

""" bug:
when checking for a frame advance, we don't check to see how many frames need
to be advanced.  a possible scenerio is an animation misses two frames b/c slow-
down, but current system will only advance once.  we need to recursively check
each frame.
"""

from states import StateDriver
from menu import TitleMenu
import engine
import gfx

import match

resource_path = "."

class Game(object):
    def __init__(self):
        engine.init()

    def load_config(self, location):
        pass

    def get_screen(self):
        return gfx.get_display()

    def start(self):
        display = gfx.get_display()

        sd = StateDriver(self)
        sd.start(TitleMenu(sd))
        #new_match = match.create_match(sd, 0, False)
        #sd.start(new_match)

        sd.run()
