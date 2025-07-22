import time
import threading
import RPi.GPIO as GPIO
import cv2 as cv
import numpy as np
from mpu6050 import mpu6050
# TODO:

running = True

TIMONTEO = 18 # Pin for steering servo

TRIG = 23 
ECHO = 24
# Pins for HC-SR04 Proximity Sensor

IN1 = 20
IN2 = 26
# Pins for L298N Motor Driver

BUTTON = 17
# Pin for starting button

ROI_MARGIN_X = 100 # Margin for marking regions of interest at edges
STEER_ANGLE = 45 # Angle for turning left or right

distance = 0 # Proximity sensor readings
direction = 0 # Right = 1, Left = -1

cw = 0 # Clockwise = 1, Counterclockwise = -1

GPIO.setmode(GPIO.BCM)
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)

GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

GPIO.setup(BUTTON, GPIO.IN)

GPIO.setup(TIMONTEO, GPIO.OUT)

tune = True # Activate tuning mode
toTune = "B" # Color to be tuned
tuneError = False

TuneHSVmin = [0,0,0]
TuneHSVmax = [0,0,0]
# For saving tuning from trackbars to file

colorList = [
    {"name":"R","HSVmin":[0,0,0],"HSVmax":[0,0,0],"contours":[]},
    {"name":"G","HSVmin":[0,0,0],"HSVmax":[0,0,0],"contours":[]},
    {"name":"B","HSVmin":[0,0,0],"HSVmax":[0,0,0],"contours":[]},
    {"name":"O","HSVmin":[0,0,0],"HSVmax":[0,0,0],"contours":[]}
]

blockCnts = [] # Block contours arranged from largest to smallest
lineCnts = [] # Line contours arranged from largest to smallest

frame = None
display = None

height = 360
width = 640

imgHSV = None
kernel = np.ones((5,5),np.uint8)

def empty(a):
    pass

def getArea(cnt) -> int:
    return cnt['area']

def distanceLoop():
    global running
    global distance
    while running:
        GPIO.output(TRIG, False)
        time.sleep(1.75)

        GPIO.output(TRIG, True)
        time.sleep(0.00001)
        GPIO.output(TRIG, False)

        while GPIO.input(ECHO) == 0:
            pulseStart = time.time()
        while GPIO.input(ECHO) == 1:
            pulseEnd = time.time()

        pulseDuration = pulseEnd - pulseStart

        distance = pulseDuration * 17150
        distance = round(distance, 2)

        #print("Distance:", distance, "cm")
def gyroLoop():
    sensor = mpu6050(0x68)
    yaw = 0.0
    gyro_z_bias = 0.0
    filtered_gyro_z = 0.0
    alpha = 0.9  # Low-pass filter coefficient

    # Calibrate gyro bias
    print("Calibrating... Keep sensor still for 3 seconds.")
    time.sleep(1)
    samples = 100
    bias_sum = 0
    for _ in range(samples):
        bias_sum += sensor.get_gyro_data()['z']
        time.sleep(0.01)
    gyro_z_bias = bias_sum / samples
    print(f"Calibrated gyro Z bias: {gyro_z_bias:.4f}°/s")

    last_time = time.time()
    try:
        while running:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time

            # Read gyro
            raw_gyro_z = sensor.get_gyro_data()['z']

            # Subtract bias
            corrected_gyro_z = raw_gyro_z - gyro_z_bias

            # Apply low-pass filter
            filtered_gyro_z = alpha * filtered_gyro_z + (1 - alpha) * corrected_gyro_z

            # Integrate to get yaw
            yaw += filtered_gyro_z * dt

            # Print or use yaw as needed
            # print(f"Yaw: {yaw:.2f}°")

            time.sleep(0.01)
    except Exception as e:
        print(f"Gyro thread stopped: {e}")

def setAngle(angle):
    max(min(angle, 60), -60) # Keeps angle within limits
    
    duty = 2 + ((angle+90) / 18)
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.45)  # Let it reach position
    pwm.ChangeDutyCycle(0)  # Stop signal to avoid jitter
    time.sleep(0.1)

def saveTuning():
    global colorList
    tuning = ""
    for color in colorList:
        if tune and toTune == color["name"]:
            color["HSVmin"] = TuneHSVmin
            color["HSVmax"] = TuneHSVmax
        tuning = "{}{},{},{},{},{},{},{},".format(tuning, color["name"], color["HSVmin"][0],color["HSVmin"][1], color["HSVmin"][2], color["HSVmax"][0],color["HSVmax"][1],color["HSVmax"][2])
        # Cycles through colorList and saves values to config file
    with open("color_tune.txt", "w") as file:
        file.write(tuning)
    print("Saved color tuning!")

def loadTuning(color:str) -> tuple:
    HSVmin = [0,0,0]
    HSVmax = [0,0,0]
    try:
        with open("color_tune.txt","r") as file:
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
    # Mask the object then apply morphologic transform to fill gaps

    masked = cv.bitwise_and(display,display,mask=mask)
    # Show colors through mask
    x,y,w,h = 0,0,0,0
    colorList[colorIdx]["contours"] = []

    cnts,hirearchy = cv.findContours(mask,cv.RETR_EXTERNAL,cv.CHAIN_APPROX_NONE)
    for cnt in cnts:
        area = cv.contourArea(cnt)
        if area>425:
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

pwm = GPIO.PWM(TIMONTEO, 50)
pwm.start(0)

def main():
    global running
    global imgHSV
    global display
    global kernel
    global direction

    if not cap.isOpened():
        print("Error: Could not open camera.")
        exit()
    # Forward
    if not tune:
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
        lineCnts = []
        if tune:
            trackColor(toTune)
        else:
            for color in colorList:
                trackColor(color["name"])
        for color in colorList:
            if color["name"] == "R" or color["name"] == "G":                     
                blockCnts.extend(color["contours"])
            if color["name"] == "B" or color["name"] == "O":                     
                lineCnts.extend(color["contours"])
        blockCnts.sort(reverse=True,key=getArea)
        # Sort block contours by area from largest to smallest
        lineCnts.sort(key=getArea)
        # Sort line contours by area from smallest to largest

        # Find the first block whose center is within the region of interest (not too close to the edges)
        closestBlock = None
        for cnt in blockCnts:
            center_x = cnt["x"] + cnt["width"] / 2
            if ROI_MARGIN_X <= center_x <= width - ROI_MARGIN_X:
                closestBlock = cnt
                break

        for cnt in blockCnts:
            cv.rectangle(display,(cnt["x"],cnt["y"]),(cnt["x"]+cnt["width"],cnt["y"]+cnt["height"]),(0,0,255),3)
            # Draw rectangle around each block
        for idx, cnt in enumerate(lineCnts):
            if not idx == 0:
                cv.rectangle(display,(cnt["x"],cnt["y"]),(cnt["x"]+cnt["width"],cnt["y"]+cnt["height"]),(0,0,0),3)
            else:
                cv.rectangle(display,(cnt["x"],cnt["y"]),(cnt["x"]+cnt["width"],cnt["y"]+cnt["height"]),(255,255,255),3)
            # Draw rectangle around each line
        if cw == 0:
            cw = {"B": 1,"O": -1}.get(lineCnts[0],"unknown")    

        lastDir = direction
        if closestBlock is not None:
            cv.rectangle(display,(closestBlock["x"],closestBlock["y"]),(closestBlock["x"]+closestBlock["width"],closestBlock["y"]+closestBlock["height"]),(0,255,0),3)
            cv.line(display,(round(closestBlock["x"]+(closestBlock["width"]/2)),0),(round(closestBlock["x"]+(closestBlock["width"]/2)),height),(255,255,0),2)
            direction = {"R": 1,"G": -1}.get(closestBlock["color"],"unknown")
            if direction != lastDir:
                setAngle(STEER_ANGLE*direction)
                # if direction changes, turn to that direction
        else:
            if distance > 70:
                direction = 0
            else:
                direction = cw
            # if no block is found and theres nothing in the way, set direction to forward
        print("TURN {}".format({1: "RIGHT",0:"FW",-1: "LEFT"}.get(direction,"unknown")))

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


if __name__ == "__main__":
    cap = cv.VideoCapture(0)
    while not GPIO.input(BUTTON) == GPIO.HIGH:
        cap.read()
        time.sleep(0.1)
    dLoop = threading.Thread(target=distanceLoop)
    gLoop = threading.Thread(target=gyroLoop)
    # steer = threading.Thread(target=setAngle)
    dLoop.start()
    gLoop.start()
    main()