# -*- coding: utf-8 -*-

"""=============================================================================

 Basically anything relating to the games "engine" goes here:
   Animation
   Loading images
   Handling input
   Handling the display, sounds, etc


...lets try not to pollute this with too much pygame stuff


also, i want to kill myself, game systems are too closely coupled to pygame,
so i guess i am stuck with using that fucking shit.
============================================================================="""

# pygame has some good utilities unrelated to graphics/sound
from pygame.time import Clock
from pygame import Rect

from match import Match

# Button Constants
BUTTON_LOW_PUNCH = 1
BUTTON_MED_PUNCH = 2
BUTTON_HI_PUNCH = 3
BUTTON_LOW_KICK = 4
BUTTON_MED_KICK = 5
BUTTON_HI_KICK = 6


# SYSTEM CONSTANTS
GAMESPEED = .02				# HOW MANY SECONDS PER GAME FRAME
MAX_FRAMES_PER_CYCLE = 2	# MAXIMUM FRAMES COMPUTED PER CYCLE

clock = Clock()

# avatars or like sprites, but support multiple animations, collision detection,
# are are not dependant on any single display library (could run them without!)
class AvatarManager(object):
	def __init__(self):
		self.update_que = set()
		self.last_update = clock.get_rawtime()

	def update_avatars(self, now):
		now = clock.get_rawtime()
		#print now, self.update_que
		for avatar in self.update_que:
			if self.last_update + avatar.current_frame.ttl >= now:
				avatar.advance_frame()
				self.draw_avatar(avatar)

		self.last_update = now

	def draw_avatar(self, avatar):
		# please extend =)
		raise NotImplementedError

	def add(self, avatar):
		self.update_que.add(avatar)

	def remove(self, avatar):
		self.update_que.remove(avatar)


# fighters have their own way to load images and sounds, dont do it here
class Game(object):
	match_factory = Match
	avatar_manager_factory = AvatarManager
	
	# load the choices for fighters, not full fighter classes
	def add_fighter_choice(self, choice):
		self.fighter_choice.add(choice)
		
	# graphics for menu, etc
	def load_graphics(self):
		pass

	def load_sounds(self):
		pass

	def load_music(self):
		pass

	def load_config(self, location):
		pass

	def start(self):
		from starter import BasicFighter
		
		self.AM = self.avatar_manager_factory()

		match = self.create_match()
		match.add_fighter(BasicFighter())
		match.run()

	def create_match(self):
		return self.match_factory()


class Avatar(object):
	# what is displayed on the screen for a GameObject

	def __init__(self, parent):
		self.animations = {}
		self.parent = parent		# the GameObject this belongs to
		self.reset()

	def advance_frame(self):
		self.current_frame_no += 1
		if self.current_frame_no >= self.ani_length:
			if self.current_ani.looping == 0:
				self.stop()
			elif self.current_ani.looping >= 0:
				self.loop()
			else:
				self.loop(True)
		else:
			self.current_frame = self.current_ani.frames[self.current_frame_no]

	def loop(self, forever = False):
		if forever:
			self.current_frame_no = self.current_ani.loop_frame
		else:
			if self.looped >= self.current_ani.looping:
				self.stop()
			else:
				self.current_frame_no = self.current_ani.loop_frame
				self.looped += 1

	def play(self, name):
		self.current_ani = self.animations[name]
		self.current_frame = self.current_ani.frames[0]
		self.current_frame_no = 0
		self.ani_length = len(self.current_ani.frames)

		# tell the manager we need to be updated
		self.avatar_manager.add(self)

	def stop(self):
		# tell the manager we no longer need updates
		self.avatar_manager.remove(self)
		self.reset()

	def reset(self):
		self.current_ani = None
		self.current_frame = None
		self.current_frame_no = 0
		self.ani_length = 0
		self.looped = 0

	def add_animation(self, name, ani):
		self.animations[name] = ani


class GameObject(object):
	# anything that lives inside a match
	# affected by game physics
	def __init__(self):
		self.avatar = Avatar(self)
		self.rect = None

	def move(self, rect):
		# internal game coords
		self.rect = rect


class Arena(object):
	def __init__(self):
		self.floor = 20
		self.height = 300
		self.width = 600


class HitBox(object):
	def __init__(self):
		self.rect = None

	def overlaps(self, other):
		pass


class PyGameKeyboardInput(object):
	def __init__(self):
		pass

	def get_key(self, event):
		if e.key == K_q:
			return BUTTON_LOW_PUNCH