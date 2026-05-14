#include <LiquidCrystal.h>

// LCD Pins
LiquidCrystal lcd(12, 11, 5, 4, 3, 2);

// Pin Definitions
int potPin = A0;
int motorEnable = 9;
int motorInput1 = 8;

// Variables
int throttle;
int speedValue;

float speed;
float current;
float voltage = 24.0;
float power;
float batteryCapacity = 240.0;
float estimatedRange;

void setup() {

  pinMode(motorEnable, OUTPUT);
  pinMode(motorInput1, OUTPUT);

  lcd.begin(16, 2);

  digitalWrite(motorInput1, HIGH);
}

void loop() {

  // Read Potentiometer
  throttle = analogRead(potPin);

  // Map Motor Speed
  speedValue = map(throttle, 0, 1023, 0, 255);

  // Run Motor
  analogWrite(motorEnable, speedValue);

  // Simulated Parameters
  speed = map(throttle, 0, 1023, 0, 80);

  current = map(throttle, 0, 1023, 1, 15);

  // Power Calculation
  power = voltage * current;

  // Range Estimation
  estimatedRange = (batteryCapacity / power) * speed;

  // LCD Display
  lcd.clear();

  // First Line
  lcd.setCursor(0, 0);
  lcd.print("Range:");
  lcd.print(estimatedRange, 1);
  lcd.print("km");

  // Second Line
  lcd.setCursor(0, 1);

  if(throttle < 300)
    lcd.print("Mode: ECO");

  else if(throttle < 700)
    lcd.print("Mode:NORMAL");

  else
    lcd.print("Mode:AGGRESS");

  delay(500);
}