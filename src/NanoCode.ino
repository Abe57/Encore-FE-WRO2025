#include <Servo.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <NewPing.h>

int TRIG = 4;
int ECHO = 3;

int FW = 6;
int BW = 5;

Servo timonteo;
NewPing sonar(TRIG, ECHO, 200);
Adafruit_MPU6050 mpu;

float yaw = 0.0;
float gyro_z_bias = 0.0;
float filtered_gyro_z = 0.0;
float alpha = 0.9;

unsigned long previousTime = 0;
unsigned long previousSensorReadMillis = 0;

void calibrateGyroBias() {
  Serial.println("Calibrating gyro... Keep still for 2 seconds.");
  int samples = 200;
  float bias_sum = 0;
  sensors_event_t a, g, temp;
  for (int i = 0; i < samples; i++) {
    mpu.getEvent(&a, &g, &temp);
    bias_sum += g.gyro.z;
    delayMicroseconds(10000);
  }
  gyro_z_bias = bias_sum / samples;
  Serial.print("Calibrated gyro Z bias: ");
  Serial.print(gyro_z_bias, 4);
  Serial.println(" rad/s");
}

void setup() {
  Serial.begin(9600);
  Serial.setTimeout(100);
  timonteo.attach(10);

  pinMode(FW, OUTPUT);
  pinMode(BW, OUTPUT);

  if (!mpu.begin()) {
    Serial.println("Failed to find MPU6050 chip");
    while (1) {
      delay(10);
    }
  }

  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
  Serial.println("MPU6050 Initialized.");

  // Wait for "START" command before proceeding
  while (true) {
    if (Serial.available() > 0) {
      String input = Serial.readString();
      input.trim();
      if (input.equalsIgnoreCase("START")) {
        Serial.println("Starting calibration...");
        break;
      }
    }
    delay(100);
  }

  calibrateGyroBias(); // <-- Calibrate gyro bias at startup

  previousTime = micros();

  Serial.println("Started!");
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readString();
    command.trim();

    if (command.startsWith("SERVO")) {
      String angleString = command.substring(5);
      int angle = angleString.toInt();
      angle = constrain(angle, -45, 45);
      timonteo.write(angle + 90);
      Serial.print("Steer Angle: ");
      Serial.print(angle);
      Serial.println("°");
    }
    else if (command.startsWith("FW"))
    {
      digitalWrite(FW, HIGH);
      digitalWrite(BW, LOW);
      Serial.println("Moving Forward");
    }
    else if (command.startsWith("BW"))
    {
      digitalWrite(FW, LOW);
      digitalWrite(BW, HIGH);
      Serial.println("Moving Backward");
    }
    else if (command.startsWith("STOP"))
    {
      digitalWrite(FW, LOW);
      digitalWrite(BW, LOW);
      Serial.println("Stopping");
    }
    else
    {
      Serial.println("Unknown command");
    }
    
  }
  handleSensorAndOrientation();
}

void handleSensorAndOrientation() {
  unsigned long currentTime = micros();
  float dt = (currentTime - previousTime) / 1000000.0;
  previousTime = currentTime;

  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);

  float raw_gyro_z = g.gyro.z;
  float corrected_gyro_z = raw_gyro_z - gyro_z_bias;
  filtered_gyro_z = alpha * filtered_gyro_z + (1 - alpha) * corrected_gyro_z;

  yaw = yaw + filtered_gyro_z * dt * (180.0 / M_PI);

  if (millis() - previousSensorReadMillis >= 100) {
    previousSensorReadMillis = millis();

    int distance = sonar.ping_cm();

    Serial.print("YAW");
    Serial.println(yaw, 2);
    Serial.print("PROX");
    Serial.println(distance);
  }
}