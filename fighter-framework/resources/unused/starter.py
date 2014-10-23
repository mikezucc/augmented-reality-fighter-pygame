# -*- coding: utf-8 -*-

from fighter import Fighter
from animation import Animation

# all the classes needed to build a basic fighter

def load_ani(files):
	ani = Animation()
	ani.load(files)
	return ani

high_kick_files = ["200.png", 30, "201.png", 30, "202.png", 30, "201.png", 30, "200.png", 30]

class BasicFighter(Fighter):
	def __init__(self):
		super(BasicFighter, self).__init__()
		self.avatar.add_animation("HIGH KICK", load_ani(high_kick_files))