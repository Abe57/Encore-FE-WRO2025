import time
import threading
import RPi.GPIO as GPIO
import cv2 as cv
import numpy as np
# TODO: 
# Steer based on block X position
# Prioritize closer (larger) blocks 
# Proximity detection steering
# Lap detection possibly based on MPU6050

TRIG = 23
ECHO = 24

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

tune = False # Activate tuning mode
toTune = "G" # Color to be tuned (R for red, G for green)

HSVminR = [0,0,0]
HSVmaxR = [0,0,0]
HSVminG = [0,0,0]
HSVmaxG = [0,0,0]

kernel = np.ones((5,5),np.uint8)

def empty(a):
    pass

def getDistance():
    GPIO.output(TRIG, True)
    time.sleep(0.1)
    GPIO.output(TRIG, False)
    # Send pulse to HC-SR04

    while GPIO.input(ECHO) == 0:
        startTime = time.time()
    while GPIO.input(ECHO) == 1:
        endTime = time.time()

    duration = endTime - startTime
    return (duration * 34300) / 2
    # Get distance in cm based on speed of sound

def distanceLoop():
    try:
        while True:
            dist = getDistance()
            print(f"Dist: {dist:.2f} cm")
            time.sleep(0.75)
    except Exception as e:
        print(f"Distance loop error: {e}")
    finally:
        GPIO.cleanup()

def saveTuning():
    with open("color_tune.txt", "w") as file:
        file.write(f"{HSVminR[0]},{HSVminR[1]},{HSVminR[2]},{HSVmaxR[0]},{HSVmaxR[1]},{HSVmaxR[2]},{HSVminG[0]},{HSVminG[1]},{HSVminG[2]},{HSVmaxG[0]},{HSVmaxG[1]},{HSVmaxG[2]}")
    print("Saved color tuning!")

def loadTuning():
    try:
        file = open("color_tune.txt","r")
    except FileNotFoundError:
        print("Tuning configuration not found, default values set to 0.")
        return
    
    global HSVminR
    global HSVmaxR
    global HSVminG
    global HSVmaxG

    values = file.readline().split(",")
    # Split file content in an array

    HSVminR = [int(values[0]),int(values[1]),int(values[2])]
    HSVmaxR = [int(values[3]),int(values[4]),int(values[5])]
    HSVminG = [int(values[6]),int(values[7]),int(values[8])]
    HSVmaxG = [int(values[9]),int(values[10]),int(values[11])]

if tune and not (toTune == "R" or toTune == "G"):
    print("Error: Color to tune undefined.")
    exit()

distance_thread = threading.Thread(target=distanceLoop, daemon=True)
distance_thread.start()
# Start distance loop in the background

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
    # Set default values to config file's stored values
def main():
    global HSVminR
    global HSVmaxR
    global HSVminG
    global HSVmaxG

    global tune
    global toTune

    global kernel
    
    cap = cv.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open camera.")
        exit()

    try:
        while True:
            ret, frame = cap.read() # Get single frame from video stream
            
            if not ret:
                print("Error: Failed to capture frame.")
                exit()
            height = 360
            width = 640
            
            frame = cv.resize(frame,(width,height))
            display = frame.copy()

            frame = cv.medianBlur(frame,15) # Average the image color
            imgHSV = cv.cvtColor(frame,cv.COLOR_BGR2HSV) # Get HSV values from image

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
            if tune:
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

            maskedR = cv.bitwise_and(display,display,mask=maskR)
            maskedG = cv.bitwise_and(display,display,mask=maskG)
            # Show colors through mask

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
                
            if cv.waitKey(1) & 0xFF == ord('q'):
                break
            time.sleep(0.005)
    except KeyboardInterrupt:
        print("Stopped by user")
    finally:
        cap.release()
        cv.destroyAllWindows()
        GPIO.cleanup()
        if tune:
            saveTuning()
        # Save tuning configuration to file if exited through pressing Q

if __name__ == "__main__":
    main()