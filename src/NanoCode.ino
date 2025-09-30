#include <Servo.h> 
#include <Wire.h> 
#include <Adafruit_MPU6050.h> 
#include <Adafruit_Sensor.h> 
#include <NewPing.h> 

#define TRIGGER_PIN_D 7
#define ECHO_PIN_D 8
#define TRIGGER_PIN_C 9
#define ECHO_PIN_C 12
#define TRIGGER_PIN_I 4
#define ECHO_PIN_I 3
#define PWM_PIN 11
#define LED_PIN 13
#define MAX_DISTANCE 200

NewPing sonar_derecho(TRIGGER_PIN_D, ECHO_PIN_D, MAX_DISTANCE);
NewPing sonar_central(TRIGGER_PIN_C, ECHO_PIN_C, MAX_DISTANCE);
NewPing sonar_izquierdo(TRIGGER_PIN_I, ECHO_PIN_I, MAX_DISTANCE);

int FW = 5; 
int BW = 6;

int motorSpeed = 255;

unsigned int dist_d = 0;
unsigned int dist_i = 0;
unsigned int dist_c = 0;

Servo timonteo; 
Adafruit_MPU6050 mpu; 

float yaw = 0.0; 
float gyro_z_bias = 0.0; 
float filtered_gyro_z = 0.0; 
float alpha = 0.9; 
unsigned long previousTime = 0; 
unsigned long previousSensorReadMillis = 0; 
char command_buffer[64];
byte buffer_pos = 0;

void calibrateGyroBias() { 
  Serial.println(F("Calibrating gyro... Keep still for 2 seconds."));
  int samples = 200; 
  float bias_sum = 0; 
  sensors_event_t a, g, temp; 
  for (int i = 0; i < samples; i++) {
    mpu.getEvent(&a, &g, &temp); 
    bias_sum += g.gyro.z; 
    delayMicroseconds(10000); 
  }
  gyro_z_bias = bias_sum / samples; 
  Serial.print(F("Calibrated gyro Z bias: "));
  Serial.print(gyro_z_bias, 4);
  Serial.println(F(" rad/s"));
}

void setup() {
  Serial.begin(9600); 
  timonteo.attach(10);
  pinMode(FW, OUTPUT); 
  pinMode(BW, OUTPUT); 
  pinMode(PWM_PIN, OUTPUT); 

  // Iniciar MPU6050
  if (!mpu.begin()) { 
    Serial.println(F("Failed to find MPU6050 chip"));
    while (1) {
      delay(10); 
    } 
  }
  mpu.setAccelerometerRange(MPU6050_RANGE_8_G); 
  mpu.setGyroRange(MPU6050_RANGE_500_DEG); 
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ); 
  Serial.println(F("MPU6050 Initialized."));
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);

  // Esperar comando "START"
  bool started = false;
  while (!started) {
    if (Serial.available() > 0) {
      char c = Serial.read();
      if (c != '\n' && buffer_pos < sizeof(command_buffer) - 1) {
        command_buffer[buffer_pos++] = c;
      } else {
        command_buffer[buffer_pos] = '\0';
        if (strcmp(command_buffer, "START") == 0) {
          started = true;
          Serial.println(F("Starting calibration..."));
        }
        buffer_pos = 0;
      }
    }
    delay(100);
  }

  calibrateGyroBias(); 
  previousTime = micros(); 
  analogWrite(PWM_PIN, 200); 
  
  Serial.println(F("Started!"));
}

void processCommand(char* command) {
    if (strncmp(command, "SERVO", 5) == 0) {
        int angle = atoi(command + 5); 
        angle = constrain(angle, -45, 45); 
        timonteo.write(angle + 90); 
        Serial.print(F("Steer Angle: "));
        Serial.print(angle);
        Serial.println(F("°"));
    } else if (strcmp(command, "FW") == 0) { 
        digitalWrite(FW, HIGH); 
        digitalWrite(BW, LOW); 
        Serial.println(F("Moving Forward"));
    } else if (strcmp(command, "BW") == 0) {
        digitalWrite(FW, LOW); 
        digitalWrite(BW, HIGH); 
        Serial.println(F("Moving Backward"));
    } else if (strcmp(command, "STOP") == 0) {
        digitalWrite(FW, LOW); 
        digitalWrite(BW, LOW); 
        Serial.println(F("Stopping"));
    } else {
        Serial.println(F("Unknown command"));
    }
}

void loop() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c != '\n' && buffer_pos < sizeof(command_buffer) - 1) {
      command_buffer[buffer_pos++] = c;
    } else {
      command_buffer[buffer_pos] = '\0';
      buffer_pos = 0;

      char* command = strtok(command_buffer, ";");
      while (command != NULL) {
        processCommand(command);
        command = strtok(NULL, ";");
      }
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

    int last = dist_d;
    dist_d = sonar_derecho.ping_cm();
    if (dist_d == 0)
    {
      dist_d = last;
    }
    last = dist_i;
    dist_i = sonar_izquierdo.ping_cm();
    if (dist_i == 0)
    {
      dist_i = last;
    }
    last = dist_c;
    dist_c = sonar_central.ping_cm();
    if (dist_c == 0)
    {
      dist_c = last;
    }
    
    Serial.print(F("YAW"));
    Serial.println(yaw, 2);
    
    Serial.print(F("PROX_R")); // Proximidad Derecha
    Serial.println(dist_d);
    
    Serial.print(F("PROX_C")); // Proximidad Central
    Serial.println(dist_c);
    
    Serial.print(F("PROX_L")); // Proximidad Izquierda
    Serial.println(dist_i);
  }
}