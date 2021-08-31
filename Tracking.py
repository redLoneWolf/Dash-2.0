import math
import urllib.request as ur
import cv2 as cv
import numpy as np
import time
import imutils
from io import BytesIO  

url = 'http://192.168.43.1:8080/shot.jpg'


OPENCV_OBJECT_TRACKERS = {
        "CSRT": cv.legacy.TrackerCSRT_create,
        "KCF": cv.legacy.TrackerKCF_create,
        "Boosting": cv.legacy.TrackerBoosting_create,
        "MIL": cv.legacy.TrackerMIL_create,
        "TLD": cv.legacy.TrackerTLD_create,
        "MedianFlow": cv.legacy.TrackerMedianFlow_create,
        "MOSSE": cv.legacy.TrackerMOSSE_create
}


# Instantiate OCV kalman filter
class KalmanFilter:

    kf = cv.KalmanFilter(4, 2)
    kf.measurementMatrix = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], np.float32)
    kf.transitionMatrix = np.array([[1, 0, 1, 0], [0, 1, 0, 1], [0, 0, 1, 0], [0, 0, 0, 1]], np.float32)

    def Estimate(self, coordX, coordY):
        ''' This function estimates the position of the object'''
        measured = np.array([[np.float32(coordX)], [np.float32(coordY)]])
        self.kf.correct(measured)
        predicted = self.kf.predict()
        return predicted



#Performs required image processing to get ball coordinated in the video
class ProcessImage:
    def __init__(self,tracker,frame,BB):
        self.tracker = OPENCV_OBJECT_TRACKERS[tracker]()

        self.kfObj = KalmanFilter()
        #predictedCoords = np.zeros((2, 1), np.float32)
        # rc, frame = vid.read()
        # imgNp = np.array(bytearray(imgResp.read()), dtype=np.uint8)
    

        # frame =  cv.imdecode(np.frombuffer(frameBytes.read(), np.uint8), -1)

        frame = imutils.resize(frame, width=500)
        (height, width) = frame.shape[:2]
        
        self.initBB = BB

        # self.initBB = cv.selectROI("Input", frame, fromCenter=False,showCrosshair=False)
        self.tracker.init(frame, self.initBB)

    
    def setTracker(self,tracker):
        self.tracker = OPENCV_OBJECT_TRACKERS[tracker]()
    
    

    def DetectObject(self,frame):
        # frame = cv.imdecode(np.frombuffer(frameBytes.read(), np.uint8), -1)
        # frame = imutils.resize(frame, width=500)
        list = self.DetectBall(frame,self.initBB)
        
        if list is not None:
            [ballX, ballY,width,height] = list
            
            predictedCoords = self.kfObj.Estimate(ballX+width/2, ballY+height/2)
            # print("BAll :" ,[predictedCoords[0], predictedCoords[1]])

            # Draw Actual coords from segmentation
            cv.circle(frame, (int(ballX+width/2), int(ballY+height/2)), 20, [0,0,255], 2, 8)
            #cv.line(frame,(int(ballX), int(ballY + 20)), (int(ballX + 50), int(ballY + 20)), [100,100,255], 2,8)
            #cv.putText(frame, "Actual", (int(ballX + 50), int(ballY + 20)), cv.FONT_HERSHEY_SIMPLEX,0.5, [50,200,250])

            # Draw Kalman Filter Predicted output
            cv.rectangle(frame, (predictedCoords[0], predictedCoords[1]), (predictedCoords[0] +20, predictedCoords[1]+5 ), (0,255,255), 2)
            cv.line(frame, (predictedCoords[0] + 16, predictedCoords[1] - 15), (predictedCoords[0] + 50, predictedCoords[1] - 30), [100, 10, 255], 2, 8)
            cv.putText(frame, "Predicted", (int(predictedCoords[0] + 50), int(predictedCoords[1] - 30)), cv.FONT_HERSHEY_SIMPLEX, 0.5, [50, 200, 250])
            return frame
            # cv.imshow('Input', frame)

            # if (cv.waitKey(1)==27 & 0xFF == ord('q')):
            #     cv.destroyAllWindows()

      

    # Segment the green ball in a given frame
    def DetectBall(self, frame,initBB):
        
        if initBB is not None:
		# grab the new bounding box coordinates of the object
                (success, box) = self.tracker.update(frame)

		# check to see if the tracking was a success
                if success:
                    (x, y, w, h) = [int(v) for v in box]
                    cv.rectangle(frame, (x, y), (x + w, y + h),(0, 255, 0), 2)
                    # print([(x, y)])
                    return [x,y,w,h]


#Main Function
def main():
    
    processImg = ProcessImage()
    processImg.DetectObject()

# if __name__ == "__main__":
#     main()


# print('Program Completed!')