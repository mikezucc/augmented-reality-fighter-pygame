augmented-reality-fighter-pygame
================================

code for rendering pygame frames and implementing opencv to simulate an augmented reality application

NOTICE:
Almost ALL of the code is written by Leif Theiden, and is under license specified in the .py files. The code relevant to the computer vision is in states.py. I used the game to just show that it can be done for others looking to get started in simple computer vision.

My code opens a thread everytime a new surface (PyGame for frame simply) is called to be displayed on the main window. I start a thread at that point and execute a simple computer vision function that does the following:

1. Searches a camera stream frame for the 5x4 chessboard (cv2.findChessboardCorners)
2. The found corners are then drawn onto the image
3. Using cv2.solvePnP, the approximate pose (Rotation and translation vectors) are derived
4. The 3d points that describe a square are then projected from the 3d space determined by step 3 into a 2d space. this is used to convert a predertimined 3d structure into something you can use to graph on a 2d image.
5. However, this step instead finds the transformation to get from a set of 2d square points (the dimensions of the game frame) to the newly found projected 2d points (of the 3d frame). Now you can see that what we are trying to is simply do a two step transformation.
6. I then perform a basic tutorial style addition of the captured stream frame and the transformed game frame to get a final image

from3dTransMatrix -> points of the projected 3d structure into 2d points. these are the red dots you see
q -> this is the reference plane that we determine the pose from
ptMatrix -> the final transformation, to transform the game frame to fit in the projected frame

enjoy!
