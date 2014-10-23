# -*- coding: utf-8 -*-
import autoblocker

from buttons import *
from fsa import FSA, LoggingFSA, STICKY
from pygame.locals import *

# def for the high framerate fighter
class KarateMan(autoblocker.AutoBlocker):
	defeat_animations = ["fall backward"]

	# A CONTROLLED GAME OBJECT WITH HEALTH BARS, A FSM

	# called to do after things like avatar has been set up

	def setup(self):
		super(KarateMan, self).setup()

		fsa = LoggingFSA(self.avatar)

		# when evualting moves, they are searched in the order inserted

		# position and movement
		fsa.add_transition(BUTTON_FORWARD, "idle", "walk forward")
		fsa.add_transition(BUTTON_BACK, "idle", "walk backward")
		fsa.add_transition(BUTTON_DOWN, "idle", "crouch")

		# normal kicks

		fsa.add_transition(BUTTON_HI_KICK, "idle", "high kick")
		fsa.add_transition(BUTTON_MED_KICK, "idle", "medium kick")
		fsa.add_transition(BUTTON_LOW_KICK, "idle", "low kick")

		# punch
		fsa.add_transition(BUTTON_HI_PUNCH, "idle", "high punch")

		# block
		fsa.add_transition(BUTTON_LOW_PUNCH, "idle", "block")

		# from block cancels
		fsa.add_transition(BUTTON_HI_PUNCH, "block", "high punch")

		# to block cancels
		fsa.add_transition(BUTTON_LOW_PUNCH, "high punch", "block", flags=STICKY)

		# crouch cancels
		fsa.add_transition(BUTTON_DOWN, "low kick", "crouch")
		fsa.add_transition(BUTTON_DOWN, "medium kick", "crouch")
		fsa.add_transition(BUTTON_DOWN, "high kick", "crouch")
		fsa.add_transition(BUTTON_DOWN, "high punch", "crouch")
		fsa.add_transition(BUTTON_DOWN, "walk forward", "crouch")
		fsa.add_transition(BUTTON_DOWN, "walk backward", "crouch")

		# crouch to sweep
		fsa.add_transition(BUTTON_KICK, "crouch", "sweep")

		# sweep to crouch while still holding down
		fsa.add_transition(BUTTON_DOWN, "sweep", "crouch", flags=STICKY)

		# jump
		fsa.add_transition(BUTTON_UP, "idle", "jump")

		# high punch cancel
		fsa.add_transition(BUTTON_HI_PUNCH, "high punch", "high punch")

		# high kick cancel
		fsa.add_transition(BUTTON_HI_KICK, "medium kick", "high kick", 2)
		fsa.add_transition(BUTTON_HI_KICK, "low kick", "high kick", 2)
		# breaking this down into frames prevents "lightning presses"
		#fsa.add_transition(BUTTON_HI_KICK, "high kick", "high kick", 1, 2)
		#fsa.add_transition(BUTTON_HI_KICK, "high kick", "high kick", 3, 3)
		#fsa.add_transition(BUTTON_HI_KICK, "high kick", "high kick", 1, 4)
		fsa.add_transition(BUTTON_HI_KICK, "high kick", "high kick", 1)

		# forward flip to jump kick cancel =)
		fsa.add_transition(BUTTON_KICK, "forward flip", "jump kick", 0, 3)
		fsa.add_transition(BUTTON_KICK, "forward flip", "jump kick", 0, 4)

		# medium kick cancel
		fsa.add_transition(BUTTON_MED_KICK, "high kick", "medium kick", 1)
		fsa.add_transition(BUTTON_MED_KICK, "low kick", "medium kick", 1)
		# breaking this down into frames prevents "lightning presses"
		#fsa.add_transition(BUTTON_MED_KICK, "medium kick", "medium kick", 1, 1)

		#fsa.add_transition(BUTTON_MED_KICK, "medium kick", "medium kick", 2, 2)
		fsa.add_transition(BUTTON_MED_KICK, "medium kick", "medium kick", 1)

		# low kick cancel
		fsa.add_transition(BUTTON_LOW_KICK, "high kick", "low kick")
		fsa.add_transition(BUTTON_LOW_KICK, "medium kick", "low kick")
		fsa.add_transition(BUTTON_LOW_KICK, "low kick", "low kick")

		# jump to jump kick cancel
		fsa.add_transition(BUTTON_KICK, "jump", "jump kick")


		# walk forward for flip
		fsa.add_transition(BUTTON_UP, "walk forward", "forward flip", 1)

		# walk backward for flip
		fsa.add_transition(BUTTON_UP, "walk backward", "backward flip", 1)

		# roundhouse to high kick cancel
		fsa.add_transition(BUTTON_HI_KICK, "roundhouse", "high kick", 1, 5)
		fsa.add_transition(BUTTON_HI_KICK, "roundhouse", "high kick", 1, 6)

		# roundhouse combo
		fsa.add_combo("roundhouse", "low kick", "medium kick", "high kick", "high kick")


		self.fsa = fsa

	# given a command, get the state, then play it
	def play_command(self, cmd, pressed):
		state = self.handle_command(cmd, pressed)
		if state != False:
			self.avatar.play(*state)

	# given a command, get the state, then return it without playing it
	def handle_command(self, cmd, pressed):

		# do a little preprocessing to simplfy direction changes
		if self.avatar.facing == 0:
			if cmd == BUTTON_LEFT:
				cmd = BUTTON_FORWARD
			elif cmd == BUTTON_RIGHT:
				cmd = BUTTON_BACK

		# do a little preprocessing to simplfy direction changes
		elif self.avatar.facing == 1:
			if cmd == BUTTON_LEFT:
				cmd = BUTTON_BACK
			elif cmd == BUTTON_RIGHT:
				cmd = BUTTON_FORWARD

		return self.fsa.process(cmd, pressed)
