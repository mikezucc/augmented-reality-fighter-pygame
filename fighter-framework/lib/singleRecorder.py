import numpy as np
import cv2

capright = cv2.VideoCapture(0)

# Define the codec and create VideoWriter object
#fourcc = cv2.VideoWriter_fourcc(*'XVID')

frameMax = 180
frameWait = 60
frameCount = 0
frameDelay = 0
while(1):
    ret, frameRight = capright.read()
    if frameDelay >= frameWait:
        cv2.circle(frameRight,(25,25), 30, (0,255,0), 5)
        if cv2.waitKey(1) & 0xFF == ord('c'):
            if (capright.isOpened()):
                
                if ret==True:
                    #frameLeft = cv2.flip(frameLeft,0)
                    # frameRight = cv2.flip(frameRight,0)

                    # write the flipped frame
                    cv2.imwrite('image' + str(frameCount) + '.png',frameRight)
                    frameCount = frameCount + 1
    else:
        cv2.circle(frameRight,(25,25), 30, (255,0,0), 5)
    cv2.imshow("dispWin", frameRight)
    frameDelay = frameDelay + 1;

# Release everything if job is finished
capright.release()
cv2.destroyAllWindows()