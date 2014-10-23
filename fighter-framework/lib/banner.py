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
from engine import DrawableObject
from avatar import StaticAvatar
from animation import Animation, AnimationFrame
import os, pygame, gc



pygame.font.init()

default_font = pygame.font.get_default_font()


class Banner(StaticAvatar):
    def __init__(self):
        super(TextBanner, self).__init__()


class TextBanner(StaticAvatar):
    def __init__(self, text, color=[0,0,0], size=12, font=None):
        super(TextBanner, self).__init__()

        self._font_size = size
        self._text      = text
        self._color     = color

        if font == None:
            self._font   = pygame.font.Font(default_font, size)
        else:
            if isinstance(font, str):
                fullpath = os.path.realpath(os.path.join(game.resource_path, font))
                self.set_font(fullpath)
            else:
                self._font = font

    def __del__(self):
        print "dying TextBanner"

    #@property
    def get_text(self):
        return self._text

    #@text.setter
    def set_text(self, text):
        self._text = text
        self.render()

    text = property(get_text, set_text)

    #@property
    def get_font(self):
        return self._font

    #@font.setter
    def set_font(self, font=None):
        if font == None:
            font = default_font
        self._font = pygame.font.Font(font, self.font_size)
        self._font_name = font
        self.render()
        
    font = property(get_font, set_font)

    #@property
    def get_font_size(self):
        return self._font_size

    #@font_size.setter
    def set_font_size(self, size):
        self._font_size = size
        self.render()

    font_size = property(get_font_size, set_font_size)

    #@property
    def get_color(self):
        return self._color

    #@color.setter
    def set_color(self, color):
        self._color = color
        self.render()

    color = property(get_color, set_color)

    def render(self):
        try:
            self.image = self.font.render(self.text, False, self._color)
            return self.image
        except AttributeError:
            print "font not set correctly"
            raise

class OutlineTextBanner(TextBanner):
    colorkey = [90,0,0]
    border = 3

    def render(self):
        try:
            image = self.font.render(self.text, False, self.colorkey)
            s = pygame.Surface(image.get_size())
            s.fill(self.colorkey)
            s.set_colorkey(self.colorkey)
            inner_font = pygame.font.Font(self._font_name, self.font_size - 4)

            text = inner_font.render(self.text, False, [0,0,0])

            for x in xrange(self.border + 2):
                for y in xrange(self.border + 2):
                    s.blit(text, (x, y))

            text = inner_font.render(self.text, False, self._color)
            s.blit(text, (2,2))

            self.image = s
            return self.image
        except AttributeError:
            print "font not set correctly"
            raise
