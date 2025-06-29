from time import sleep
import cv2 as cv
import numpy as np
#TODO: 
# Steer based on block X position
# Prioritize closer (larger) blocks 
# Proximity detection steering
# Lap detection possibly based on MPU6050

tune = False # Activate tuning mode
toTune = "R" # Color to be tuned (R for red, G for green)

HSVminR = [0,0,0]
HSVmaxR = [0,0,0]
HSVminG = [0,0,0]
HSVmaxG = [0,0,0]

kernel = np.ones((5,5),np.uint8)

def empty(a):
    pass

def saveTuning():
    with open("color_tune.txt", "w") as file:
        file.write(f"{HSVminR[0]},{HSVminR[1]},{HSVminR[2]},{HSVmaxR[0]},{HSVmaxR[1]},{HSVmaxR[2]},{HSVminG[0]},{HSVminG[1]},{HSVminG[2]},{HSVmaxG[0]},{HSVmaxG[1]},{HSVmaxG[2]}")
    print("Saved color tuning!")

def loadTuning():
    global HSVminR
    global HSVmaxR
    global HSVminG
    global HSVmaxG

    file = open("color_tune.txt","r")
    values = file.readline().split(",")

    HSVminR = [int(values[0]),int(values[1]),int(values[2])]
    HSVmaxR = [int(values[3]),int(values[4]),int(values[5])]
    
    HSVminG = [int(values[6]),int(values[7]),int(values[8])]
    HSVmaxG = [int(values[9]),int(values[10]),int(values[11])]

if tune and not (toTune == "R" or toTune == "G"):
    print("Error: Color to tune was not defined.")
    exit()

loadTuning()

if tune:
    cv.namedWindow("trackbars")
    cv.resizeWindow("trackbars",720,430)
    if toTune == "R":
        cv.createTrackbar("Hue Min","trackbars", HSVminR[0], 180, empty)
        cv.createTrackbar("Sat Min","trackbars", HSVminR[1], 255, empty)
        cv.createTrackbar("Val Min","trackbars", HSVminR[2], 255, empty)
        cv.createTrackbar("Hue Max","trackbars", HSVmaxR[0], 180, empty)
        cv.createTrackbar("Sat Max","trackbars", HSVmaxR[1], 255, empty)
        cv.createTrackbar("Val Max","trackbars", HSVmaxR[2], 255, empty)
    elif toTune == "G":
        cv.createTrackbar("Hue Min","trackbars", HSVminG[0], 180, empty)
        cv.createTrackbar("Sat Min","trackbars", HSVminG[1], 255, empty)
        cv.createTrackbar("Val Min","trackbars", HSVminG[2], 255, empty)
        cv.createTrackbar("Hue Max","trackbars", HSVmaxG[0], 180, empty)
        cv.createTrackbar("Sat Max","trackbars", HSVmaxG[1], 255, empty)
        cv.createTrackbar("Val Max","trackbars", HSVmaxG[2], 255, empty)

cap = cv.VideoCapture(2)

if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

while True:
    ret, frame = cap.read()

    if not ret:
        print("Error: Failed to capture frame.")
        exit()
    height = 360
    width = 640
    
    frame = cv.resize(frame,(width,height))
    display = frame.copy()

    frame = cv.medianBlur(frame,15) #Average the image color
    imgHSV = cv.cvtColor(frame,cv.COLOR_BGR2HSV) #Get HSV values from image

    if tune:
        Hmin = cv.getTrackbarPos("Hue Min","trackbars")
        Vmin = cv.getTrackbarPos("Val Min","trackbars")
        Smin = cv.getTrackbarPos("Sat Min","trackbars")

        Hmax = cv.getTrackbarPos("Hue Max","trackbars")
        Smax = cv.getTrackbarPos("Sat Max","trackbars")
        Vmax = cv.getTrackbarPos("Val Max","trackbars")
        if toTune == "R":
            HSVminR = [Hmin,Smin,Vmin]
            HSVmaxR = [Hmax,Smax,Vmax]
        elif toTune == "G":
            HSVminG = [Hmin,Smin,Vmin]
            HSVmaxG = [Hmax,Smax,Vmax]
        # Edit tuning
    
    print("Red:",HSVminR[0],HSVmaxR[0],HSVminR[1],HSVmaxR[1],HSVminR[2],HSVmaxR[2])
    print("Green:",HSVminG[0],HSVmaxG[0],HSVminG[1],HSVmaxG[1],HSVminG[2],HSVmaxG[2])

    lowerR = np.array(HSVminR)
    upperR = np.array(HSVmaxR)
    lowerG = np.array(HSVminG)
    upperG = np.array(HSVmaxG)
    # Define threshold

    maskR = cv.inRange(imgHSV,lowerR,upperR)
    maskG = cv.inRange(imgHSV,lowerG,upperG)
    maskR = cv.dilate(maskR,kernel,iterations=3)
    maskG = cv.dilate(maskG,kernel,iterations=3)
    maskR = cv.erode(maskR,kernel, iterations=2)
    maskG = cv.erode(maskG,kernel,iterations=2)
    # Mask the object, dilate then erode to fill gaps

    maskedR = cv.bitwise_and(frame,frame,mask=maskR)
    maskedG = cv.bitwise_and(frame,frame,mask=maskG)

    cntsR,hirearchy = cv.findContours(maskR,cv.RETR_EXTERNAL,cv.CHAIN_APPROX_NONE)
    for cnt in cntsR:
        area = cv.contourArea(cnt)
        if area>425 and not (toTune == "G" and tune):
            cv.drawContours(maskedR,cnt,-1,(255,0,0),3)
            peri = cv.arcLength(cnt,True)
            approx = cv.approxPolyDP(cnt,0.02*peri,True)
            xR,yR,wR,hR = cv.boundingRect(approx)
            cv.rectangle(display,(xR,yR),(xR+wR,yR+hR),(0,0,255),3)
            cv.line(display,(round(xR+(wR/2)),0),(round(xR+(wR/2)),height),(255,255,0),2)

    cntsG,hirearchy = cv.findContours(maskG,cv.RETR_EXTERNAL,cv.CHAIN_APPROX_NONE)
    for cnt in cntsG:
        area = cv.contourArea(cnt)
        if area>350 and not (toTune == "R" and tune):
            cv.drawContours(maskedG,cnt,-1,(255,0,0),3)
            peri = cv.arcLength(cnt,True)
            approx = cv.approxPolyDP(cnt,0.02*peri,True)
            xG,yG,wG,hG = cv.boundingRect(approx)
            cv.rectangle(display,(xG,yG),(xG+wG,yG+hG),(0,0,255),3)
            cv.line(display,(round(xG+(wG/2)),0),(round(xG+(wG/2)),height),(255,255,0),2)
    # Get average position of large enough detected objects
    
    cv.imshow("Image",display)
    if toTune == "R" and tune:
        cv.imshow("Red Mask",maskedR)
    elif toTune == "G" and tune:
        cv.imshow("Green Mask",maskedG)

    sleep(0.005)

    if cv.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
if tune:
    saveTuning()
    # Save tuning configuration to file if exited through pressing Q
