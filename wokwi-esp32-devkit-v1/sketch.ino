#include <Wire.h>

#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

#include <OneWire.h>
#include <DallasTemperature.h>

// ---------------- PIN DEFINITIONS ----------------

#define SDA_PIN 21
#define SCL_PIN 22

#define THROTTLE_PIN 34

#define ONE_WIRE_PIN 4

#define START_BUTTON 18
#define STOP_BUTTON 19
#define RESET_BUTTON 23

#define GREEN_LED 25
#define BLUE_LED 26
#define RED_LED 27

// ---------------- OLED ----------------

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64

Adafruit_SSD1306 display(
  SCREEN_WIDTH,
  SCREEN_HEIGHT,
  &Wire,
  -1
);

// ---------------- SENSORS ----------------

Adafruit_MPU6050 mpu;

OneWire oneWire(ONE_WIRE_PIN);
DallasTemperature temperatureSensor(&oneWire);

// ---------------- SETUP ----------------

void setup() {

  Serial.begin(115200);

  delay(2000);

  Serial.println();
  Serial.println("==============================");
  Serial.println("ESP32 STARTED");
  Serial.println("==============================");

  // GPIO

  Serial.println("STEP 1: GPIO");

  pinMode(THROTTLE_PIN, INPUT);

  pinMode(START_BUTTON, INPUT_PULLUP);
  pinMode(STOP_BUTTON, INPUT_PULLUP);
  pinMode(RESET_BUTTON, INPUT_PULLUP);

  pinMode(GREEN_LED, OUTPUT);
  pinMode(BLUE_LED, OUTPUT);
  pinMode(RED_LED, OUTPUT);

  digitalWrite(GREEN_LED, LOW);
  digitalWrite(BLUE_LED, LOW);
  digitalWrite(RED_LED, LOW);

  Serial.println("GPIO OK");

  // I2C

  Serial.println("STEP 2: I2C");

  Wire.begin(SDA_PIN, SCL_PIN);

  Serial.println("I2C OK");

  // OLED

  Serial.println("STEP 3: OLED");

  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {

    Serial.println("OLED FAILED");

  } else {

    Serial.println("OLED OK");

    display.clearDisplay();

    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);

    display.setCursor(0, 0);
    display.println("EV SYSTEM");

    display.setCursor(0, 15);
    display.println("Initializing...");

    display.display();
  }

  // MPU6050

  Serial.println("STEP 4: MPU6050");

  if (!mpu.begin(0x68)) {

    Serial.println("MPU6050 NOT FOUND");

  } else {

    Serial.println("MPU6050 OK");

    mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
    mpu.setGyroRange(MPU6050_RANGE_500_DEG);
    mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
  }

  // DS18B20

  Serial.println("STEP 5: DS18B20");

  temperatureSensor.begin();

  Serial.println("DS18B20 OK");

  // COMPLETE

  Serial.println("==============================");
  Serial.println("SETUP COMPLETE");
  Serial.println("==============================");

  display.clearDisplay();

  display.setCursor(0, 0);
  display.println("EV SYSTEM");

  display.setCursor(0, 15);
  display.println("READY");

  display.display();
}

// ---------------- LOOP ----------------

void loop() {

  Serial.println("SYSTEM RUNNING");

  delay(2000);
}