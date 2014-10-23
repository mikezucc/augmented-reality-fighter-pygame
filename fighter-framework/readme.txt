Fighter Framework


While this game you've downloaded looks like IK, it really is a test for the
library that could be used for simple games that have a fighting theme.

Main features of FF are:
	Super smooth animation control using an FSA (see fsa.py)
	Customizable input with button and move cancels and combos
	Animation system that uses folders and text files for organization
	Animation frames can attack, block and be damaged with hitboxes
	Hit confirms
	Low use of system resources
	Simple API for fighters - see fighter.py
	Simple graphics system that works like pygame sprites
	Simple menus
	Simple state management
	Customizable match types (although only one is written here)

The IK part of the demo is:
	Sprites ripped from C64 game
	Sounds ripped from Enter the Dragon
	Some attacks can be "held" like the original
	Controls modified to take advantage of multiple buttons
	AI players

Feel free to play the game and send me any ideas or improvements!


Combos and special moves:
================================================================================
  LK, MK, HK, HK  => Roundhouse Kick   (hit the buttons quickly)
            J, K  => Jumping Kick      (hit any kick during the jump)
         Back, J  => Backflip
      Forward, J  => Frontflip


P1 Default keys:
Q:    LK
W:    MK
E:    HK
A:    Block*
D:    P
F:    (F)lip.  Turn character around.
Up:   Jump
Down: Crouch.  (try kicking)

Attack Holds
In the original IK, attacks could be "held" on the attack frame.  This is also
implemented here by holding down that attack button.