# -*- coding: utf-8 -*-
import unittest


class AnimationFrameTC(unittest.TestCase):
	def setUp(self):
		import animation
		self.frame = animation.AnimationFrame()

class AnimationTC(unittest.TestCase):
	def setUp(self):
		import animation
		self.animation = animation.Animation

	def testCanAddFrame(self):
		frame = animation.AnimationFrame
		self.animation.add(frame)
		# assert....

class WorldTC(unittest.TestCase):
	import engine
	def setUp(self):
		self.world = engine.World()

	def testCanAddDrawableObject(self):
		obj = engine.DrawableObject()
		self.world.add_object(obj)

	def testCanAddUpdateableObject(self):
		obj = engine.UpdateableObject()
		self.world.add_object(obj)

	def testCanAddDrawableObject(self):
		obj = engine.DrawableObject()
		self.world.add_object(obj)

	def testCanRemoveObject(self):
		self.testCanAddDrawableObject(self)
		self.world.remove_object(obj)

def suite():
	tcs = map(unittest.makeSuite,[y for x,y in globals().items() if x[-2:] == "TC"])
	return unittest.TestSuite(tcs)

if __name__ == '__main__':
	testSuite = suite()
	runner = unittest.TextTestRunner()
	runner.run(testSuite)