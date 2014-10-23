# -*- coding: utf-8 -*-

"""=============================================================================

 Let's extend our base engine for PyGame


...we can pollute this with pygame stuff
============================================================================="""


import pygame, os
from pygame.time import Clock
from pygame import Rect

from engine import *


# from Francis Stokes
def load_image(fullname, colorkey=None):
	try:
		image = pygame.image.load(fullname)
	except pygame.error, message:
		print 'Cannot load image:', fullname
		raise SystemExit, message
	image = image.convert()
	if colorkey is not None:
		if colorkey is -1:
			colorkey = image.get_at((0,0))
		image.set_colorkey(colorkey, RLEACCEL)
	return image, image.get_rect()



class PyGameAvatarManager(AvatarManager):
	def __init__(self):
		super(PyGameAvatarManager, self).__init__()
		self.surface = None

	def draw_avatar(self, avatar):
		avatar.current_frame.draw(surface, avatar.parent.rect)


class PyGameGame(Game):					# no, that's not a typo
	avatar_manager_factory = PyGameAvatarManager

	def __init__(self):
		super(PyGameGame, self).__init__()
		self.display = None

		self.setup_display()

		# put initial menu, etc here

		# no menus, just go to a fight!

	def setup_display(self):
		os.environ['SDL_VIDEO_CENTERED'] = "1"
		pygame.init()
		pygame.display.set_caption("Fighter v0.1.5")

		screen = pygame.display.set_mode((400, 300))

		#Background Set Up
		background = pygame.Surface(screen.get_size())
		background = background.convert()
		background.fill((0,0,0))

		self.display = screen


