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

running = True

TRIG = 23
ECHO = 24

IN1 = 20
IN2 = 26

ROI_MARGIN_X = 100

GPIO.setmode(GPIO.BCM)
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)

GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

tune = True # Activate tuning mode
toTune = "R" # Color to be tuned
tuneError = False

TuneHSVmin = [0,0,0]
TuneHSVmax = [0,0,0]

colorList = [
    {"name": "R","HSVmin":[0,0,0],"HSVmax":[0,0,0],"contours":[]},
    {"name":"G","HSVmin":[0,0,0],"HSVmax":[0,0,0],"contours":[]}
]

blockCnts = []

curFollow = {}

frame = None
display = None

height = 360
width = 640

imgHSV = None
kernel = np.ones((5,5),np.uint8)

def empty(a):
    pass

def getArea(cont):
    return cont['area']

def distanceLoop():
    global running
    while running:
        GPIO.output(TRIG, False)
        time.sleep(1.75)

        GPIO.output(TRIG, True)
        time.sleep(0.00001)
        GPIO.output(TRIG, False)

        while GPIO.input(ECHO) == 0:
            pulse_start = time.time()
        while GPIO.input(ECHO) == 1:
            pulse_end = time.time()

        pulse_duration = pulse_end - pulse_start

        distance = pulse_duration * 17150
        distance = round(distance, 2)

        print("Distance:", distance, "cm")

def saveTuning():
    global colorList
    tuning = ""
    for color in colorList:
        if tune and toTune == color["name"]:
            color["HSVmin"] = TuneHSVmin
            color["HSVmax"] = TuneHSVmax
        tuning = "{}{},{},{},{},{},{},{},".format(tuning, color["name"], color["HSVmin"][0],color["HSVmin"][1], color["HSVmin"][2], color["HSVmax"][0],color["HSVmax"][1],color["HSVmax"][2])
    with open("color_tune.txt", "w") as file:
        file.write(tuning)
    print("Saved color tuning!")

def loadTuning(color:str) -> list:
    HSVmin = [0,0,0]
    HSVmax = [0,0,0]
    try:
        file = open("color_tune.txt","r")
    except FileNotFoundError:
        print("Tuning configuration not found, default values set to 0.")
        return

    indexOffset = 0
    values = file.readline().split(",")
    for i in colorList:
        if color == values[indexOffset]:
            HSVmin = [int(values[indexOffset+1]),int(values[indexOffset+2]),int(values[indexOffset+3])]
            HSVmax = [int(values[indexOffset+4]),int(values[indexOffset+5]),int(values[indexOffset+6])]
        indexOffset += 7
    # Search through config file for color values

    return HSVmin, HSVmax

def trackColor(color:str):
    global imgHSV
    global display
    global colorList

    global TuneHSVmin
    global TuneHSVmax

    for colorVal in colorList:
        if colorVal["name"] == color:
            HSVmin = colorVal["HSVmin"]
            HSVmax = colorVal["HSVmax"]

    if tune:
        cv.namedWindow("trackbars")
        cv.resizeWindow("trackbars",720,430)

        TuneHSVmin[0] = cv.getTrackbarPos("Hue Min","trackbars")
        TuneHSVmin[1] = cv.getTrackbarPos("Sat Min","trackbars")
        TuneHSVmin[2] = cv.getTrackbarPos("Val Min","trackbars")

        TuneHSVmax[0] = cv.getTrackbarPos("Hue Max","trackbars")
        TuneHSVmax[1] = cv.getTrackbarPos("Sat Max","trackbars")
        TuneHSVmax[2] = cv.getTrackbarPos("Val Max","trackbars")
        if toTune == color:
            HSVmin = TuneHSVmin
            HSVmax = TuneHSVmax
        # Edit tuning

    lower = np.array(HSVmin)
    upper = np.array(HSVmax)
    # Define threshold

    mask = cv.inRange(imgHSV,lower,upper)
    mask = cv.morphologyEx(mask,cv.MORPH_OPEN,kernel)
    # Mask the object then apply morphologic transform to fill gaps

    masked = cv.bitwise_and(display,display,mask=mask)
    # Show colors through mask
    x,y,w,h = 0,0,0,0
    i = 0
    for colorVal in colorList:
        if colorVal["name"] == color:
            colorList[i]["contours"] = []
        i += 1

    cnts,hirearchy = cv.findContours(mask,cv.RETR_EXTERNAL,cv.CHAIN_APPROX_NONE)
    for cnt in cnts:
        area = cv.contourArea(cnt)
        if area>425:
            peri = cv.arcLength(cnt,True)
            approx = cv.approxPolyDP(cnt,0.02*peri,True)
            x,y,w,h = cv.boundingRect(approx)
            if (toTune == color and tune) or not tune:
                cv.drawContours(masked,cnt,-1,(255,0,0),3)
            i = 0
            for colorVal in colorList:
                if colorVal["name"] == color:
                    colorList[i]["contours"].append({"color":color,"contour":cnt,"area":area,"x":x,"y":y,"width":w,"height":h})
                i += 1
    if toTune == color and tune:
        cv.imshow(f"{color} Mask",masked)
for color in colorList:
    if toTune == color["name"]:
        tuneError = False
        continue
if tuneError and tune:
    print("Error: Color to tune undefined.")
    exit()

i = 0
for color in colorList:
    colorList[i]["HSVmin"],colorList[i]["HSVmax"] = loadTuning(color["name"])
    i += 1
# Load tuning for all colors in colorList

if tune:
    for colorVal in colorList:
        if toTune == colorVal["name"]:
            break
    cv.namedWindow("trackbars")
    cv.resizeWindow("trackbars",720,430)
    cv.createTrackbar("Hue Min","trackbars", colorVal["HSVmin"][0], 180, empty)
    cv.createTrackbar("Sat Min","trackbars", colorVal["HSVmin"][1], 255, empty)
    cv.createTrackbar("Val Min","trackbars", colorVal["HSVmin"][2], 255, empty)
    cv.createTrackbar("Hue Max","trackbars", colorVal["HSVmax"][0], 180, empty)
    cv.createTrackbar("Sat Max","trackbars", colorVal["HSVmax"][1], 255, empty)
    cv.createTrackbar("Val Max","trackbars", colorVal["HSVmax"][2], 255, empty)

#distance_thread = threading.Thread(target=distanceLoop, daemon=True)
#distance_thread.start()
# Start distance loop in the background

def main():
    global running
    global imgHSV
    global display
    global kernel

    cap = cv.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open camera.")
        exit()
    # Forward
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)

    while running:
        ret, frame = cap.read() # Get single frame from video stream

        if not ret:
            print("Error: Failed to capture frame.")
            exit()

        frame = cv.resize(frame,(width,height))
        display = frame.copy()

        frame = cv.medianBlur(frame,15) # Average the image color
        frame = cv.bilateralFilter(frame, 11, 75, 75)
        imgHSV = cv.cvtColor(frame,cv.COLOR_BGR2HSV) # Get HSV values from image
        cv.line(display,(ROI_MARGIN_X,0),(ROI_MARGIN_X,height),(255,0,255),2)
        cv.line(display,(width-ROI_MARGIN_X,0),(width-ROI_MARGIN_X,height),(255,0,255),2)

        blockCnts = []
        if tune:
            trackColor(toTune)
        else:
            for color in colorList:
                trackColor(color["name"])
        for color in colorList:
            if color["name"] == "R" or color["name"] == "G":                     
                for cnt in color["contours"]:
                    blockCnts.append(cnt)
                    
        blockCnts.sort(reverse=True,key=getArea)
        for cnt in blockCnts:
            cv.rectangle(display,(cnt["x"],cnt["y"]),(cnt["x"]+cnt["width"],cnt["y"]+cnt["height"]),(0,0,255),3)
        try:
            cv.rectangle(display,(blockCnts[0]["x"],blockCnts[0]["y"]),(blockCnts[0]["x"]+blockCnts[0]["width"],blockCnts[0]["y"]+blockCnts[0]["height"]),(0,255,0),3)
            if not (blockCnts[0]["x"]+(blockCnts[0]["width"])/2 < ROI_MARGIN_X or blockCnts[0]["x"]+(blockCnts[0]["width"])/2 > width-ROI_MARGIN_X):
                cv.line(display,(round(blockCnts[0]["x"]+(blockCnts[0]["width"]/2)),0),(round(blockCnts[0]["x"]+(blockCnts[0]["width"]/2)),height),(255,255,0),2)
            else:
                cv.line(display,(round(blockCnts[0]["x"]+(blockCnts[0]["width"]/2)),0),(round(blockCnts[0]["x"]+(blockCnts[0]["width"]/2)),height),(0,255,255),2)
        except IndexError:
            pass

        cv.imshow("Image",display)

        if cv.waitKey(1) & 0xFF == ord('q'):
            running = False
            break
        time.sleep(0.05)

    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    cap.release()
    cv.destroyAllWindows()
    if tune:
        saveTuning()
    # Save tuning configuration to file if exited through pressing Q

dLoop = threading.Thread(target=distanceLoop)

dLoop.start()

if __name__ == "__main__":
    main()