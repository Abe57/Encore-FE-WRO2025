import os
import serial
import time
import threading
import RPi.GPIO as GPIO
import cv2 as cv
import numpy as np
from mpu6050 import mpu6050
# TODO:

running = True # Controls if the program is running
ready = False # Indicates if the robot is ready to receive commands

command = ""

BUTTON = 17 # Pin for starting button
SERIAL_PORT = '/dev/ttyUSB0' # Serial port for communication with the robot

ROI_MARGIN_X = 100 # Margin for marking regions of interest at edges

MIN_DIST = 30 # Minimum distance to consider for turning
STEER_ANGLE = 35 # Angle for turning left or right

distance = 0 # Proximity sensor readings
direction = 0 # Right = 1, Left = -1
yaw = 0.00 # Yaw angle from gyro sensor

angGiro = 0.00 # Angle to match when turning


cw = 0 # Clockwise = 1, Counterclockwise = -1

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

tune = False # Activate tuning mode
toTune = "O" # Color to be tuned
tuneError = False # Error if toTune is not in colorList

FirstRound = True # Flag to indicate if it's the first round of match
canStop = False # Flag to indicate if the robot can stop

TuneHSVmin = [0,0,0]
TuneHSVmax = [0,0,0]
# For saving tuning from trackbars to file

colorList = [
    {"name":"R","HSVmin":[0,0,0],"HSVmax":[0,0,0],"contours":[]},
    {"name":"G","HSVmin":[0,0,0],"HSVmax":[0,0,0],"contours":[]},
    {"name":"B","HSVmin":[0,0,0],"HSVmax":[0,0,0],"contours":[]},
    {"name":"O","HSVmin":[0,0,0],"HSVmax":[0,0,0],"contours":[]}
]
# List of colors with their HSV min and max values, and contours
# R = Red, G = Green, B = Blue, O = Orange

blockCnts = [] # Block contours arranged from largest to smallest
lineCnts = [] # Line contours arranged from largest to smallest

frame = None # Frame captured from camera
display = None # Frame to be displayed in window
imgHSV = None # HSV values of the frame

height = 360
width = 640
# Set resolution of camera

kernel = np.ones((5,5),np.uint8) # Kernel for morphological operations

def empty(a):
    pass 
    # Placeholder function for trackbars

def getArea(cnt) -> int:
    return cnt['area']
    # Function to get area of contour for sorting
def getY(cnt) -> int:
    return cnt['y']
    # Function to get y coordinate of contour for sorting

def serialCommsLoop():
    global running, distance, yaw, ready, command, canStop
    try:
        ser = serial.Serial(SERIAL_PORT, 9600, timeout=1)
        print(f"Connected to {SERIAL_PORT} at 9600 baud.")
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='replace').strip()
                if line == "Started!":
                    ready = True
                elif not ready:
                    ser.write(b"START\n")
                if ready:
                    if line.startswith("PROX"):
                        try:
                            getStuff = float(line[len("PROX"):].strip())
                            if getStuff != 0:
                                distance = getStuff
                        except ValueError:
                            pass
                    elif line.startswith("YAW"):
                        try:
                            yaw = float(line[len("YAW"):].strip())
                        except ValueError:
                            pass
                    elif line == "Stopping":
                        print("Stopping")
                        canStop = True
                        ser.write(f"{command}\n".encode('utf-8'))                                     
                        break
                    ser.write(f"{command}\n".encode('utf-8'))                                     
    except serial.SerialException as e:
        print(f"Serial error: {e}")
    except Exception as e:
        print(f"Serial thread error: {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
def saveTuning():
    global colorList
    tuning = ""
    for color in colorList:
        if tune and toTune == color["name"]:
            color["HSVmin"] = TuneHSVmin
            color["HSVmax"] = TuneHSVmax
        tuning = "{}{},{},{},{},{},{},{},".format(tuning, color["name"], color["HSVmin"][0],color["HSVmin"][1], color["HSVmin"][2], color["HSVmax"][0],color["HSVmax"][1],color["HSVmax"][2])
        # Cycles through colorList and saves values to config file
    with open(os.path.expanduser("~/EncoreFileSharing/color_tune.txt"), "w") as file:
        file.write(tuning)
    print("Saved color tuning!")

def loadTuning(color:str) -> tuple:
    HSVmin = [0,0,0]
    HSVmax = [0,0,0]
    try:
        with open(os.path.expanduser("~/EncoreFileSharing/color_tune.txt"),"r") as file:
            values = file.readline().split(",")
    except FileNotFoundError:
        print("Tuning configuration not found, default values set to 0.")
        return

    indexOffset = 0
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

    for idx,colorVal in enumerate(colorList):
        if colorList[idx]["name"] == color:
            colorIdx = idx
            HSVmin = colorVal["HSVmin"]
            HSVmax = colorVal["HSVmax"]
            break
            # Cycle through colorList to get min and max HSV
    if tune:
        cv.namedWindow("trackbars")
        cv.resizeWindow("trackbars",720,430)

        TuneHSVmin[0] = cv.getTrackbarPos("Hue Min","trackbars")
        TuneHSVmin[1] = cv.getTrackbarPos("Sat Min","trackbars")
        TuneHSVmin[2] = cv.getTrackbarPos("Val Min","trackbars")

        TuneHSVmax[0] = cv.getTrackbarPos("Hue Max","trackbars")
        TuneHSVmax[1] = cv.getTrackbarPos("Sat Max","trackbars")
        TuneHSVmax[2] = cv.getTrackbarPos("Val Max","trackbars")
        # Get values from trackbars if in tuning mode
        if toTune == color:
            HSVmin = TuneHSVmin
            HSVmax = TuneHSVmax
        # Edit tuning

    lower = np.array(HSVmin)
    upper = np.array(HSVmax)
    # Define threshold

    mask = cv.inRange(imgHSV,lower,upper)
    mask = cv.morphologyEx(mask,cv.MORPH_OPEN,kernel)
    mask = cv.morphologyEx(mask,cv.MORPH_CLOSE,kernel)  # Add closing to fill small holes
    # Mask the object then apply morphologic transform to fill gaps

    masked = cv.bitwise_and(display,display,mask=mask)
    # Show colors through mask
    x,y,w,h = 0,0,0,0
    colorList[colorIdx]["contours"] = []

    cnts,hirearchy = cv.findContours(mask,cv.RETR_EXTERNAL,cv.CHAIN_APPROX_NONE)
    for cnt in cnts:
        area = cv.contourArea(cnt)
        if area > 800:  # Increase area threshold to ignore small noise
            peri = cv.arcLength(cnt,True)
            approx = cv.approxPolyDP(cnt,0.02*peri,True)
            x,y,w,h = cv.boundingRect(approx)
            # Get bounding rectangle for contour
            if (toTune == color and tune) or not tune:
                cv.drawContours(masked,cnt,-1,(255,0,0),3)
                colorList[colorIdx]["contours"].append({"color": color, "area": area, "x": x, "y": y, "width": w, "height": h})
    if toTune == color and tune:
        cv.imshow(f"{color} Mask",masked)
for color in colorList:
    if toTune == color["name"]:
        tuneError = False
        continue
if tuneError and tune:
    print("Error: Color to tune undefined.")
    exit()

for idx, color in enumerate(colorList):
    colorList[idx]["HSVmin"],colorList[idx]["HSVmax"] = loadTuning(colorList[idx]["name"])
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
    # Create trackbars for tuning color values

def main():
    global running
    global imgHSV
    global display
    global kernel
    global direction
    global command
    global cw
    global ready

    global distance
    global yaw
    global canStop
    global angGiro

    if not cap.isOpened():
        print("Error: Could not open camera.")
        exit()
    if not tune:
        command = "FW"
    while not ready:
        time.sleep(0.1)
    while running:
        ret, frame = cap.read() # Get single frame from video stream

        if not ret:
            print("Error: Failed to capture frame.")
            exit()

        frame = cv.resize(frame,(width,height)) # Rescale frame to specified resolution
        frame = cv.rotate(frame, cv.ROTATE_180) # Rotate frame to correct orientation
        display = frame.copy()

        # --- Noise reduction pipeline ---
        frame = cv.GaussianBlur(frame, (7, 7), 0)  # Add Gaussian blur
        frame = cv.medianBlur(frame, 5)            # Use smaller median blur kernel
        frame = cv.bilateralFilter(frame, 9, 75, 75) # Optional: keep bilateral filter, but smaller kernel
        imgHSV = cv.cvtColor(frame,cv.COLOR_BGR2HSV) # Get HSV values from image
        # --- End noise reduction pipeline ---

        cv.line(display,(ROI_MARGIN_X,0),(ROI_MARGIN_X,height),(255,0,255),2)
        cv.line(display,(width-ROI_MARGIN_X,0),(width-ROI_MARGIN_X,height),(255,0,255),2)
        # Draw lines to mark regions of interest at edges

        blockCnts = []
        lineCnts = []
        # Clear previous contours
        
        if tune:
            trackColor(toTune)
        else:
            # Only track "B" and "O" on the first round, otherwise track all
            if FirstRound:
                for color in colorList:
                    if color["name"] in ["B", "O"]:
                        trackColor(color["name"])
            else:
                for color in colorList:
                    trackColor(color["name"])
        # Track colors in colorList
        
        for color in colorList:
            if color["name"] == "R" or color["name"] == "G":                     
                blockCnts.extend(color["contours"])
            if color["name"] == "B" or color["name"] == "O":                     
                lineCnts.extend(color["contours"])
        # Separate contours into blocks and lines based on color
        
        blockCnts.sort(reverse=True,key=getArea) # Sort block contours by area from largest to smallest
        lineCnts.sort(key=getY) # Sort line contours by y coordinate from top to bottom

        closestBlock = None # Find the first block whose center is within the region of interest (not too close to the edges)
        
        for cnt in blockCnts:
            center_x = cnt["x"] + cnt["width"] / 2
            if ROI_MARGIN_X <= center_x <= width - ROI_MARGIN_X:
                closestBlock = cnt
                break
        # Look for the closest block within the region of interest

        for cnt in blockCnts:
            cv.rectangle(display,(cnt["x"],cnt["y"]),(cnt["x"]+cnt["width"],cnt["y"]+cnt["height"]),(0,0,255),3)
            # Draw rectangle around each block
        for idx, cnt in enumerate(lineCnts):
            if not idx == 0:
                cv.rectangle(display,(cnt["x"],cnt["y"]),(cnt["x"]+cnt["width"],cnt["y"]+cnt["height"]),(0,0,0),3)
            else:
                cv.rectangle(display,(cnt["x"],cnt["y"]),(cnt["x"]+cnt["width"],cnt["y"]+cnt["height"]),(255,255,255),3)
            # Draw rectangle around each line
            
        line_colors = set(cnt["color"] for cnt in lineCnts)
        if cw == 0 and "B" in line_colors and "O" in line_colors:
            cw = {"B": 1,"O": -1}.get(lineCnts[0]["color"],"unknown")
            print("DIRECTION SET TO ",cw)

        lastDir = direction
        if (closestBlock is not None) or not FirstRound:
            cv.rectangle(display,(closestBlock["x"],closestBlock["y"]),(closestBlock["x"]+closestBlock["width"],closestBlock["y"]+closestBlock["height"]),(0,255,0),3)
            cv.line(display,(round(closestBlock["x"]+(closestBlock["width"]/2)),0),(round(closestBlock["x"]+(closestBlock["width"]/2)),height),(255,255,0),2)
            direction = {"R": 1,"G": -1}.get(closestBlock["color"],"unknown")
        else:
            if distance > MIN_DIST and angGiro < abs(yaw):
                direction = 0
            else:
                direction = cw
                if angGiro < abs(yaw):
                    angGiro = abs(yaw) + 90
            # if no block is found and theres nothing in the way, set direction to forward
        if direction != lastDir:
            command = f"SERVO{STEER_ANGLE*direction}"
            print("TURN {}".format({1: "RIGHT",0:"FW",-1: "LEFT"}.get(direction,"unknown")))
            # if direction changes, turn to that direction

        cv.imshow("Image",display)
        #print(f"Distance: {distance}, Yaw: {yaw}")

        if (cv.waitKey(1) & 0xFF == ord('q')) or abs(yaw) > 1090:
            command = "STOP"
            running = False
            break
        time.sleep(0.1) # Sleep to reduce CPU usage
    while not canStop:
        if tune:
            break
        time.sleep(0.1)

    cap.release()
    cv.destroyAllWindows()
    # Stop motors and clean up GPIO
    if tune:
        saveTuning()
    # Save tuning configuration to file if exited through pressing Q

def buttonCheck():
    global running,command
    while running:
        if not GPIO.input(BUTTON) == GPIO.HIGH:
            break
    while running:
        if GPIO.input(BUTTON) == GPIO.HIGH:
            command = "STOP"
            running = False
            break
        time.sleep(0.01)

if __name__ == "__main__":
    if not tune:
        commsThread = threading.Thread(target=serialCommsLoop, daemon=True)
        commsThread.start()
    command = "SERVO0"  # Initialize command to stop servo
    ready = tune
    while not ready:
        time.sleep(0.1)
    cap = cv.VideoCapture(0)
    print("Press start button")
    while not GPIO.input(BUTTON) == GPIO.HIGH:  # Wait for button press to start
        cap.read()
        time.sleep(0.01)
    bLoop = threading.Thread(target=buttonCheck)  # Add watcher thread
    bLoop.start()
    main()
