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

import game
import pygame, os.path, sys



DEBUG = False

def debug(text):
    if DEBUG: sys.stdout.write(text)


sound_cache = {}

class NoSound:
    def play(self): pass
    def stop(self): pass

dummy = NoSound()

def load_sound(name):
    global sound_cache

    if not pygame.mixer:
        debug("Cannot load sound: pygame.mixer not ready\n")
        return dummy

    # um fix this?
    #fullpath = os.path.join('fighters', 'ik_guy', 'sounds', name)
    fullpath = os.path.join(game.resource_path, name)

    # try to the the cach first
    try:
        return sound_cache[fullpath]
    except KeyError:
        pass

    # pygame will load a sound even if it doesn't exist... do a sanity check.
    open(fullpath).close()

    try:
        sound = pygame.mixer.Sound(fullpath)
    except pygame.error, message:
        debug("Cannot load sound: %s\n" % fullpath)
        debug("%s\n" % message)
        return dummy

    # update the cache
    sound_cache[fullpath] = sound

    return sound
