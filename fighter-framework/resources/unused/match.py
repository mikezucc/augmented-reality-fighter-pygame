# -*- coding: utf-8 -*-

class Match(object):
	def __init__(self):
		self.fighters = []
		self.style = None			# 1v1, 2v1, 2v2, tag, etc

	# LOAD = from file, or directory
	def load_fighters(self, fighters):
		raise NotImplementedError

	# add a Fighter class object to the match, not a file
	def add_fighter(self, fighter):
		self.fighters.append(fighter)
		fighter.move((100, 200))

	def run(self):
		self.pre_run()
		finished = False

		# clock.time is pygame: how many ms since last time tick() was called
		while finished == False:
			dt = clock.tick()
			max = MAX_FRAMES_PER_CYCLE
			while dt > 0 and max:
				dt -= GAMESPEED
				max -= 1
				self.AM.update_avatars(dt)
				self.do_cycle(GAMESPEED)

		def do_cycle(self, speed):
			# when moved to module, make "do_cycle" module-level func (PERFORMANCE)
			# this is for framerate independant stuff.  physics, etc.
			pass

# testing
	def pre_run(self):
		self.fighters[0].avatar.play("HIGH KICK")