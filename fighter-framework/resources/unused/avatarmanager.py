# -*- coding: utf-8 -*-

# the AvatarManager (AM) controls animated sprites and determines drawing.
# somewhat like a sprite group.  includes layers.

# kicking it old school with a module as class and globals. weee....!?

import time,sys

import avatar
import gfx

DEBUG = False

def debug(text):
	if DEBUG: sys.stdout.write(text)



all_avatars = set()
update_que = set()
last_update = {}

def initialize():
	global all_avatars, last_update, update_que

	all_avatars = set()
	update_que = set()		# list of avatars to be updated (not just drawn)
	last_update = {}

def update_avatars():
	global all_avatars, last_update, update_que

	now = time.time() * 1000

	[ a.update(now) for a in update_que ]

def handle_attacks(attacks):
	for frame, hit_box, target, dmg_box in attacks:
		if dmg_box == None:
			if frame.sound_miss != None:
				frame.sound_miss.play()
		else:
			if frame.sound_hit != None:
				frame.sound_hit.play()
			global_screen.fill([0,0,255], dmg_box)
			global_screen.fill([255,0,0], hit_box)
			pygame.display.update()

def add(avatar):
	global last_update, update_que

	update_que.add(avatar)
	last_update[avatar] = None

def remove(avatar):
	global last_update, update_que

	try:
		update_que.remove(avatar)
		del last_update[avatar]
	except ValueError:
		pass

def draw_avatars(avatars, surface, background=None):
	# surface should be a buffer, background should be unmodified background
	dirty = []

	for avatar in avatars:
		# some frames can change the position of the avatar
		# check for it and update if nessisary
		pos = list(avatar.position)
		frame = avatar.current_frame

		others = [ a.current_frame.rect for a in self.all_avatars if a != avatar ]
		c = avatar.current_frame.rect.collidelist(others)
		if c > -1:
			print "collision", avatar.current_frame.rect, others[c]

		# clip to reduce the size of a dirty rect blit (not working!)
		try:
			clip = frame.rect.clip(avatar.previous_frame.rect)
			if DRAW_DEBUG:
				print "clipped!", clip
				global_screen.fill([255,255,255], clip)
				draw_debug()
		except AttributeError:
			pass

		if frame.sound != None:
			frame.sound.play()

		if frame.move_avatar != (0,0):
			pos[0] = pos[0] + frame.move_avatar[0]
			pos[1] = pos[1] + frame.move_avatar[1]
			avatar.position = pos
			frame.update()

		debug("drawing: %s\n" % frame)

		# where we draw...
		dirty.append(frame.draw(surface, pos))

	return dirty
