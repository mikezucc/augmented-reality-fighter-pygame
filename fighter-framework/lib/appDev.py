import numpy as np
import cv2
import glob

def cameraCalib():
    # termination criteria
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    # prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
    objp = np.zeros((5*4,3), np.float32)
    objp[:,:2] = np.mgrid[0:5,0:4].T.reshape(-1,2)

    # Arrays to store object points and image points from all the images.
    objpoints = [] # 3d point in real world space
    imgpoints = [] # 2d points in image plane.

    images = glob.glob('./recorded/*.png')

    img = cv2.imread(images[0])
    cv2.imshow('test',img)

    meanErrList = []
    matrixList = []

    for fname in images:
        img = cv2.imread(fname)
        gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

        # Find the chess board corners
        ret, corners = cv2.findChessboardCorners(gray, (5,4),None)

        # If found, add object points, image points (after refining them)
        if ret == True:
            objpoints.append(objp)

            cv2.cornerSubPix(gray,corners,(11,11),(-1,-1),criteria)
            imgpoints.append(corners)

            # Draw and display the corners
            cv2.drawChessboardCorners(img, (5,4), corners,ret)
            cv2.imshow('img',img)

            ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1],None,None)

            mean_error = 0
            tot_error = 0
            for i in xrange(len(objpoints)):
                imgpoints2, _ = cv2.projectPoints(objpoints[i], rvecs[i], tvecs[i], mtx, dist)
                error = cv2.norm(imgpoints[i],imgpoints2, cv2.NORM_L2)/len(imgpoints2)
                tot_error += error

            mean_error = tot_error/(len(xrange(len(objpoints))))
            total_error = mean_error/len(objpoints)
            print "total error: ", total_error

            meanErrList.append(total_error)
            matrixList.append([mtx, dist, rvecs, tvecs])

            cv2.waitKey(100)

    numpyMeanErrList = np.asarray(meanErrList)
    #print min(meanErrList)
    print np.amin(numpyMeanErrList)
    minErrIdx = meanErrList.index(min(meanErrList))
    selCalibData = matrixList[minErrIdx]
    #print selCalibData
    np.save("calibDataMTX",selCalibData[0])
    np.save("calibDataDIST",selCalibData[1])
    np.save("calibDataRVECS",selCalibData[2])
    np.save("calibDataTVECS",selCalibData[3])
    loadedCalibFileMTX = np.load('calibDataMTX.npy')
    loadedCalibFileDIST = np.load('calibDataDIST.npy')
    loadedCalibFileRVECS = np.load('calibDataRVECS.npy')
    loadedCalibFileTVECS = np.load('calibDataTVECS.npy')
    print loadedCalibFileMTX
    print loadedCalibFileDIST
    print loadedCalibFileRVECS
    print loadedCalibFileTVECS
    mtx = loadedCalibFileMTX[0]
    dist = loadedCalibFileDIST[0]
    rvecs = loadedCalibFileRVECS[0]
    tvecs = loadedCalibFileTVECS[0]
    print mtx
    print dist
    print rvecs
    print tvecs

cameraCalib()