augmented-reality-fighter-pygame
================================

https://www.youtube.com/watch?v=b8PMgRdXlZE

https://www.youtube.com/watch?v=s-IiAD5H5YU

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

#How to setup:

Set up OpenCV 3.0.0 alpha
1. Follow the instructions from the website, but generally you need install a whole suite of libraries like numpy 1.9 and scipy. There was not a straight forward out of the box for me. As of time of edit, the opencv.org site seems to be down (the docs are still up)

Initial configuration for this code

1.  Run the singleRecorder.py to capture around 18-22 frames of the checkerboard in various poses with as little blur or fuzziness as possible. Use the 'c' key to capture a frame you want.
2.  Run the cameraCalib function in appDev.py to obtain the intrinsic camera parameters and distortion data which is stored as calibDataMTX.npy and calibDataDIST.npy. These you need to import to the fighter-framework directory and the lib directory.

Check out the screens in the topmost folder ;]

enjoy!
