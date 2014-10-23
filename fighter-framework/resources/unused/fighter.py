# -*- coding: utf-8 -*-

from engine import Avatar, GameObject

class Fighter(GameObject):
	# A CONTROLLED GAME OBJECT WITH HEALTH BARS
	def __init__(self):
		super(Fighter, self).__init__()
		self.hp = 100
		self.controller = None

	# commands are expressed as constants
	def handle_command(self, cmd):
		self.avatar.play(cmd)


