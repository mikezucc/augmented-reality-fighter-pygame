# -*- coding: utf-8 -*-

#try for event based system

"""
image/animation loading should be done at runtime, during "matchup screen"
load all for animations, and convert them

centeralized "animation" server.  ie, i don't want every sprite checking
if they should advance frames or not.

"call back" system, sounds good, but i want to reduce function call overhead,
stupid slow python....


an image's center, is always the lower left corner


time dependant rendering

can moves "hold" on a frame?  ie, hold the button, hold the kick, etc?


"""

import pygame

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

	
# very basic, doesn't support images
class AnimationFrame(object):
	__slots__ = ["image", "rect", "hb_attack", "hb_exposed", "hold", "ttl"]

	def __init__(self):
		self.image = None		# speaks for itself, i think
		self.rect = None 		# bbox
		self.hb_attack = None	# where an attack is decided on a foe
		self.hb_exposed = None	# where the frame can be attacked
		self.ttl = 0 			# how many ms until flipped to next
		self.hold = False		# frames won't advance when key is held
		self.play_sound = None	# play a sound when frame is displayed
		self.move_avatar = (0,0)	# this frame will move the avatar

	def load(self, image):
		raise NotImplementedError

	def draw(self):
		raise NotImplementedError
		

class PyGameAnimationFrame(AnimationFrame):
	# I want a little more control over the sprites, so I am not going to use
	# pygame's Sprite class.  it's a bit too restrictive.
	# (i want to control updates)
	def __init__(self):
		super(PyGameAnimationFrame, self).__init__()
		self.image = None
		self.rect = None
		
	def draw(self, surface, rect):
		surface.blit(self.image, rect)
			
	def load(self, file):
		self.image, self.rect = load_image(file)
				

class Animation(object):
	# is no caching frame server, (may not be needed yet)
	frame_factory = PyGameAnimationFrame

	def __init__(self):
		self.name = None
		self.frames = []
		self.modifier = 0 	# modify the playback speed (should be percent)
		self.looping = -1	# if > 0, then loop that many times.  -1 = forever
		self.loop_frame = 0	# if looping, then where to start again

	def load(self, frame_list):
		# array must be formatted:
		# [file_name, ttl, ...]
		for [file_name, ttl] in zip(*[iter(frame_list)]*2):
			frame = self.frame_factory()
			frame.load(file_name)
			frame.ttl = ttl
			print "loaded", file_name, frame, len(self.frames)
			self.frames.append(frame)
